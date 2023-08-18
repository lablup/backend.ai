import asyncio
import grp
import logging
import multiprocessing
import os
import pwd
import ssl
import sys
from pathlib import Path
from pprint import pprint
from typing import Any, AsyncIterator, Sequence

import aiomonitor
import aiotools
import click
from aiohttp import web
from setproctitle import setproctitle

from ai.backend.common.config import ConfigurationError, override_key, redis_config_iv
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.events import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.logging import BraceStyleAdapter, Logger
from ai.backend.common.types import LogSeverity
from ai.backend.common.utils import env_info

from . import __version__ as VERSION
from .api.client import init_client_app
from .api.manager import init_manager_app
from .config import load_local_config, load_shared_config
from .context import Context

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@aiotools.server
async def server_main_logwrapper(loop, pidx, _args):
    setproctitle(f"backend.ai: storage-proxy worker-{pidx}")
    try:
        asyncio.get_child_watcher()
    except (AttributeError, NotImplementedError):
        pass
    log_endpoint = _args[1]
    logger = Logger(_args[0]["logging"], is_master=False, log_endpoint=log_endpoint)
    with logger:
        async with server_main(loop, pidx, _args):
            yield


async def check_migration(ctx: Context):
    from .migration import check_latest

    await check_latest(ctx)


@aiotools.server
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Sequence[Any],
) -> AsyncIterator[None]:
    local_config = _args[0]
    loop.set_debug(local_config["debug"]["asyncio"])
    m = aiomonitor.Monitor(
        loop,
        port=local_config["storage-proxy"]["aiomonitor-port"] + pidx,
        console_enabled=False,
        hook_task_factory=local_config["debug"]["enhanced-aiomonitor-task-info"],
    )
    m.prompt = f"monitor (storage-proxy[{pidx}@{os.getpid()}]) >>> "
    m.console_locals["local_config"] = local_config
    aiomon_started = False
    try:
        m.start()
        aiomon_started = True
    except Exception as e:
        log.warning("aiomonitor could not start but skipping this error to continue", exc_info=e)

    try:
        etcd = load_shared_config(local_config)
        try:
            redis_config = redis_config_iv.check(
                await etcd.get_prefix("config/redis"),
            )
            log.info(f"PID: {pidx} - configured redis_addr: {redis_config['addr']}")
        except Exception as e:
            log.exception("Unable to read config from etcd")
            raise e

        event_producer = await EventProducer.new(
            redis_config,
            db=REDIS_STREAM_DB,
            log_events=local_config["debug"]["log-events"],
        )
        log.info(f"PID: {pidx} - Event producer created. (addr: {redis_config['addr']})")
        event_dispatcher = await EventDispatcher.new(
            redis_config,
            db=REDIS_STREAM_DB,
            log_events=local_config["debug"]["log-events"],
            node_id=local_config["storage-proxy"]["node-id"],
        )
        log.info(f"PID: {pidx} - Event dispatcher created. (addr: {redis_config['addr']})")
        ctx = Context(
            pid=os.getpid(),
            local_config=local_config,
            etcd=etcd,
            event_producer=event_producer,
            event_dispatcher=event_dispatcher,
        )
        m.console_locals["ctx"] = ctx
        client_api_app = await init_client_app(ctx)
        manager_api_app = await init_manager_app(ctx)
        m.console_locals["client_api_app"] = client_api_app
        m.console_locals["manager_api_app"] = manager_api_app

        if pidx == 0:
            await check_migration(ctx)

        client_ssl_ctx = None
        manager_ssl_ctx = None
        if local_config["api"]["client"]["ssl-enabled"]:
            client_ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            client_ssl_ctx.load_cert_chain(
                str(local_config["api"]["client"]["ssl-cert"]),
                str(local_config["api"]["client"]["ssl-privkey"]),
            )
        if local_config["api"]["manager"]["ssl-enabled"]:
            manager_ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            manager_ssl_ctx.load_cert_chain(
                str(local_config["api"]["manager"]["ssl-cert"]),
                str(local_config["api"]["manager"]["ssl-privkey"]),
            )
        client_api_runner = web.AppRunner(client_api_app)
        manager_api_runner = web.AppRunner(manager_api_app)
        await client_api_runner.setup()
        await manager_api_runner.setup()
        client_service_addr = local_config["api"]["client"]["service-addr"]
        manager_service_addr = local_config["api"]["manager"]["service-addr"]
        client_api_site = web.TCPSite(
            client_api_runner,
            str(client_service_addr.host),
            client_service_addr.port,
            backlog=1024,
            reuse_port=True,
            ssl_context=client_ssl_ctx,
        )
        manager_api_site = web.TCPSite(
            manager_api_runner,
            str(manager_service_addr.host),
            manager_service_addr.port,
            backlog=1024,
            reuse_port=True,
            ssl_context=manager_ssl_ctx,
        )
        await client_api_site.start()
        await manager_api_site.start()
        if os.geteuid() == 0:
            uid = local_config["storage-proxy"]["user"]
            gid = local_config["storage-proxy"]["group"]
            os.setgroups(
                [g.gr_gid for g in grp.getgrall() if pwd.getpwuid(uid).pw_name in g.gr_mem],
            )
            os.setgid(gid)
            os.setuid(uid)
            log.info("Changed process uid:gid to {}:{}", uid, gid)
        log.info("Started service.")
        try:
            yield
        finally:
            log.info("Shutting down...")
            await manager_api_runner.cleanup()
            await client_api_runner.cleanup()
            await event_producer.close()
            await event_dispatcher.close()
    finally:
        if aiomon_started:
            m.close()


@click.group(invoke_without_command=True)
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=Path,
    default=None,
    help=(
        "The config file path. "
        "(default: ./storage-proxy.toml and /etc/backend.ai/storage-proxy.toml)"
    ),
)
@click.option(
    "--debug",
    is_flag=True,
    help="This option will soon change to --log-level TEXT option.",
)
@click.option(
    "--log-level",
    type=click.Choice(LogSeverity, case_sensitive=False),
    default=LogSeverity.INFO,
    help="Choose logging level from... debug, info, warning, error, critical",
)
@click.pass_context
def main(
    cli_ctx,
    config_path: Path,
    log_level: LogSeverity,
    debug: bool = False,
) -> int:
    if debug:
        click.echo("Please use --log-level options instead")
        click.echo("--debug options will soon change to --log-level TEXT option.")
        log_level = LogSeverity.DEBUG

    try:
        local_config = load_local_config(config_path, debug=debug)
    except ConfigurationError:
        raise click.Abort()
    override_key(local_config, ("logging", "level"), log_level.name)
    override_key(local_config, ("logging", "pkg-ns", "ai.backend"), log_level.name)

    multiprocessing.set_start_method("spawn")

    if cli_ctx.invoked_subcommand is None:
        local_config["storage-proxy"]["pid-file"].write_text(str(os.getpid()))
        ipc_base_path = local_config["storage-proxy"]["ipc-base-path"]
        log_sockpath = Path(
            ipc_base_path / f"storage-proxy-logger-{os.getpid()}.sock",
        )
        log_sockpath.parent.mkdir(parents=True, exist_ok=True)
        log_endpoint = f"ipc://{log_sockpath}"
        local_config["logging"]["endpoint"] = log_endpoint
        try:
            logger = Logger(
                local_config["logging"],
                is_master=True,
                log_endpoint=log_endpoint,
            )
            with logger:
                setproctitle("backend.ai: storage-proxy")
                log.info("Backend.AI Storage Proxy", VERSION)
                log.info("Runtime: {0}", env_info())
                log.info("Node ID: {0}", local_config["storage-proxy"]["node-id"])
                log_config = logging.getLogger("ai.backend.agent.config")
                if local_config["debug"]["enabled"]:
                    log_config.debug("debug mode enabled.")
                if "debug" in local_config and local_config["debug"]["enabled"]:
                    print("== Storage proxy configuration ==")
                    pprint(local_config)
                if local_config["storage-proxy"]["event-loop"] == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                aiotools.start_server(
                    server_main_logwrapper,
                    num_workers=local_config["storage-proxy"]["num-proc"],
                    args=(local_config, log_endpoint),
                )
                log.info("exit.")
        finally:
            if local_config["storage-proxy"]["pid-file"].is_file():
                # check is_file() to prevent deleting /dev/null!
                local_config["storage-proxy"]["pid-file"].unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
