import asyncio
import json
import shlex
import sys
from typing import Dict, List, MutableMapping, Optional, Sequence, Union

import aiohttp
import click

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode

from ..compat import asyncio_run, asyncio_run_forever
from ..config import DEFAULT_CHUNK_SIZE
from ..request import Request
from ..session import AsyncSession
from ..versioning import get_naming
from .pretty import print_error, print_fail, print_info, print_warn


class WSProxy:
    __slots__ = (
        "api_session",
        "session_name",
        "app_name",
        "args",
        "envs",
        "reader",
        "writer",
    )

    def __init__(
        self,
        api_session: AsyncSession,
        session_name: str,
        app_name: str,
        args: MutableMapping[str, Union[None, str, List[str]]],
        envs: MutableMapping[str, str],
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self.api_session = api_session
        self.session_name = session_name
        self.app_name = app_name
        self.args = args
        self.envs = envs
        self.reader = reader
        self.writer = writer

    async def run(self) -> None:
        prefix = get_naming(self.api_session.api_version, "path")
        path = f"/stream/{prefix}/{self.session_name}/tcpproxy"
        params = {"app": self.app_name}

        if len(self.args.keys()) > 0:
            params["arguments"] = json.dumps(self.args)
        if len(self.envs.keys()) > 0:
            params["envs"] = json.dumps(self.envs)

        api_rqst = Request("GET", path, b"", params=params, content_type="application/json")
        async with api_rqst.connect_websocket() as ws:

            async def downstream() -> None:
                try:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.ERROR:
                            await self.write_error(msg)
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSE:
                            if msg.data != aiohttp.WSCloseCode.OK:
                                await self.write_error(msg)
                            break
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            self.writer.write(msg.data)
                            await self.writer.drain()
                except ConnectionResetError:
                    pass  # shutting down
                except asyncio.CancelledError:
                    pass
                finally:
                    self.writer.close()
                    try:
                        await self.writer.wait_closed()
                    except (BrokenPipeError, IOError):
                        # closed
                        pass

            down_task = asyncio.create_task(downstream())
            try:
                while True:
                    chunk = await self.reader.read(DEFAULT_CHUNK_SIZE)
                    if not chunk:
                        break
                    await ws.send_bytes(chunk)
            except ConnectionResetError:
                pass  # shutting down
            except asyncio.CancelledError:
                raise
            finally:
                if not down_task.done():
                    down_task.cancel()
                    await down_task

    async def write_error(self, msg: aiohttp.WSMessage) -> None:
        if isinstance(msg.data, bytes):
            error_msg = msg.data.decode("utf8")
        else:
            error_msg = str(msg.data)
        rsp = (
            "HTTP/1.1 503 Service Unavailable\r\n"
            "Connection: Closed\r\n\r\n"
            "WebSocket reply: {}".format(error_msg)
        )
        self.writer.write(rsp.encode())
        await self.writer.drain()


class ProxyRunnerContext:
    __slots__ = (
        "session_name",
        "app_name",
        "protocol",
        "host",
        "port",
        "args",
        "envs",
        "api_session",
        "local_server",
        "exit_code",
    )

    session_name: str
    app_name: str
    protocol: str
    host: str
    port: int
    args: Dict[str, Union[None, str, List[str]]]
    envs: Dict[str, str]
    api_session: Optional[AsyncSession]
    local_server: Optional[asyncio.AbstractServer]
    exit_code: int

    def __init__(
        self,
        host: str,
        port: int,
        session_name: str,
        app_name: str,
        *,
        protocol: str = "tcp",
        args: Sequence[str] = None,
        envs: Sequence[str] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.session_name = session_name
        self.app_name = app_name
        self.protocol = protocol

        self.api_session = None
        self.local_server = None
        self.exit_code = 0

        self.args, self.envs = {}, {}
        if args is not None and len(args) > 0:
            for argline in args:
                tokens = []
                for token in shlex.shlex(argline, punctuation_chars=True):
                    kv = token.split("=", maxsplit=1)
                    if len(kv) == 1:
                        tokens.append(shlex.split(token)[0])
                    else:
                        tokens.append(kv[0])
                        tokens.append(shlex.split(kv[1])[0])

                if len(tokens) == 1:
                    self.args[tokens[0]] = None
                elif len(tokens) == 2:
                    self.args[tokens[0]] = tokens[1]
                else:
                    self.args[tokens[0]] = tokens[1:]
        if envs is not None and len(envs) > 0:
            for envline in envs:
                split = envline.strip().split("=", maxsplit=2)
                if len(split) == 2:
                    self.envs[split[0]] = split[1]
                else:
                    self.envs[split[0]] = ""

    async def handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        assert self.api_session is not None
        p = WSProxy(
            self.api_session,
            self.session_name,
            self.app_name,
            self.args,
            self.envs,
            reader,
            writer,
        )
        try:
            await p.run()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print_error(e)

    async def __aenter__(self) -> None:
        self.exit_code = 0
        self.api_session = AsyncSession()
        await self.api_session.__aenter__()

        user_url_template = "{protocol}://{host}:{port}"
        try:
            compute_session = self.api_session.ComputeSession(self.session_name)
            all_apps = await compute_session.stream_app_info()
            for app_info in all_apps:
                if app_info["name"] == self.app_name:
                    if "url_template" in app_info.keys():
                        user_url_template = app_info["url_template"]
                    break
            else:
                print_fail(f'The app "{self.app_name}" is not supported by the session.')
                self.exit_code = 1
                return

            self.local_server = await asyncio.start_server(
                self.handle_connection, self.host, self.port
            )
            user_url = user_url_template.format(
                protocol=self.protocol,
                host=self.host,
                port=self.port,
            )
            print_info(
                'A local proxy to the application "{0}" '.format(self.app_name)
                + 'provided by the session "{0}" '.format(self.session_name)
                + "is available at:\n{0}".format(user_url),
            )
            if self.host == "0.0.0.0":
                print_warn(
                    'NOTE: Replace "0.0.0.0" with the actual hostname you use '
                    "to connect with the CLI app proxy."
                )
        except Exception:
            await self.api_session.__aexit__(*sys.exc_info())
            raise

    async def __aexit__(self, *exc_info) -> None:
        if self.local_server is not None:
            print_info("Shutting down....")
            self.local_server.close()
            await self.local_server.wait_closed()
        assert self.api_session is not None
        await self.api_session.__aexit__(*exc_info)
        assert self.api_session.closed
        if self.local_server is not None:
            print_info('The local proxy to "{}" has terminated.'.format(self.app_name))
        self.local_server = None


@main.command()
@click.argument("session_name", type=str, metavar="NAME")
@click.argument("app", type=str)
@click.option(
    "-b",
    "--bind",
    type=str,
    default="127.0.0.1:8080",
    metavar="[HOST:]PORT",
    help="The IP/host address and the port number to bind this proxy.",
)
@click.option(
    "--arg",
    type=str,
    multiple=True,
    metavar='"--option <value>"',
    help="Add additional argument when starting service.",
)
@click.option(
    "-e",
    "--env",
    type=str,
    multiple=True,
    metavar='"ENVNAME=envvalue"',
    help="Add additional environment variable when starting service.",
)
def app(session_name, app, bind, arg, env):
    """
    Run a local proxy to a service provided by Backend.AI compute sessions.

    The type of proxy depends on the app definition: plain TCP or HTTP.

    \b
    SESSID: The compute session ID.
    APP: The name of service provided by the given session.
    """
    bind_parts = bind.rsplit(":", maxsplit=1)
    if len(bind_parts) == 1:
        host = "127.0.0.1"
        port = int(bind_parts[0])
    elif len(bind_parts) == 2:
        host = bind_parts[0]
        port = int(bind_parts[1])
    try:
        proxy_ctx = ProxyRunnerContext(
            host,
            port,
            session_name,
            app,
            protocol="tcp",
            args=arg,
            envs=env,
        )
        asyncio_run_forever(proxy_ctx)
        sys.exit(proxy_ctx.exit_code)
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)


@main.command()
@click.argument("session_name", type=str, metavar="SESSION_ID", nargs=1)
@click.argument("app_name", type=str, metavar="APP", nargs=-1)
@click.option("-l", "--list-names", is_flag=True, help="Just print all available services.")
def apps(session_name, app_name, list_names):
    """
    List available additional arguments and environment variables when starting service.

    \b
    SESSID: The compute session ID.
    APP: The name of service provided by the given session. Repeatable.
         If none provided, this will print all available services.
    """

    async def print_arguments():
        apps = []
        async with AsyncSession() as api_session:
            compute_session = api_session.ComputeSession(session_name)
            apps = await compute_session.stream_app_info()
            if len(app_name) > 0:
                apps = list(filter(lambda x: x["name"] in app_name))
        if list_names:
            print_info(
                "This session provides the following app services: {0}".format(
                    ", ".join(list(map(lambda x: x["name"], apps)))
                )
            )
            return
        for service in apps:
            has_arguments = "allowed_arguments" in service.keys()
            has_envs = "allowed_envs" in service.keys()

            if has_arguments or has_envs:
                print_info("Information for service {0}:".format(service["name"]))
                if has_arguments:
                    print("\tAvailable arguments: {0}".format(service["allowed_arguments"]))
                if has_envs:
                    print("\tAvailable environment variables: {0}".format(service["allowed_envs"]))
            else:
                print_info(
                    "Service {0} does not have customizable arguments.".format(service["name"])
                )

    try:
        asyncio_run(print_arguments())
    except Exception as e:
        print_error(e)
