from __future__ import annotations

import asyncio
import functools
import grp
import logging
import os
import pwd
import ssl
import sys
import traceback
import uuid
from collections.abc import Iterable, Mapping, Sequence
from contextlib import asynccontextmanager as actxmgr
from logging import LoggerAdapter
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Final,
    Optional,
    cast,
)

import aiohttp_cors
import aiomonitor
import aiotools
import click
from aiohttp import web
from aiohttp.typedefs import Middleware
from setproctitle import setproctitle

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.metrics.http import (
    build_api_metric_middleware,
    build_prometheus_metrics_handler,
)
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
from ai.backend.common.types import HostPortPair
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel

from .config import AccountManagerConfig, ServerConfig
from .config import load as load_config
from .context import CleanupContext, RootContext
from .exceptions import (
    BackendError,
    GenericBadRequest,
    InternalServerError,
    MethodNotAllowed,
    URLNotFound,
)
from .types import AppCreator, EventLoopType, WebRequestHandler

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


global_subapp_pkgs: Final[tuple[str, ...]] = (
    ".auth",
    ".application",
)


@web.middleware
async def api_middleware(request: web.Request, handler: WebRequestHandler) -> web.StreamResponse:
    _handler = handler
    method_override = request.headers.get("X-Method-Override", None)
    if method_override:
        request = request.clone(method=method_override)
        new_match_info = await request.app.router.resolve(request)
        if new_match_info is None:
            raise InternalServerError("No matching method handler found")
        _handler = new_match_info.handler
        request._match_info = new_match_info  # type: ignore  # this is a hack
    ex = request.match_info.http_exception
    if ex is not None:
        # handled by exception_middleware
        raise ex
    request_id = request.headers.get("X-BackendAI-RequestID", str(uuid.uuid4()))
    request["request_id"] = request_id
    request["log"] = BraceStyleAdapter(logging.getLogger(f"{__spec__.name} - #{request_id}"))  # type: ignore[name-defined]
    resp = await _handler(request)
    return resp


@web.middleware
async def exception_middleware(
    request: web.Request, handler: WebRequestHandler
) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    log: LoggerAdapter = request["log"]

    try:
        resp = await handler(request)
    except BackendError as ex:
        if ex.status_code == 500:
            log.warning("Internal server error raised inside handlers")
        raise
    except web.HTTPException as ex:
        if ex.status_code == 404:
            raise URLNotFound(extra_data=request.path)
        if ex.status_code == 405:
            concrete_ex = cast(web.HTTPMethodNotAllowed, ex)
            raise MethodNotAllowed(
                method=concrete_ex.method, allowed_methods=concrete_ex.allowed_methods
            )
        log.warning("Bad request: {0!r}", ex)
        raise GenericBadRequest
    except asyncio.CancelledError as e:
        # The server is closing or the client has disconnected in the middle of
        # request.  Atomic requests are still executed to their ends.
        log.debug("Request cancelled ({0} {1})", request.method, request.rel_url)
        raise e
    except Exception as e:
        log.exception("Uncaught exception in HTTP request handlers {0!r}", e)
        if root_ctx.local_config.debug.enabled:
            raise InternalServerError(traceback.format_exc())
        else:
            raise InternalServerError()
    else:
        return resp


async def hello(request: web.Request) -> web.Response:
    return web.Response()


async def on_prepare(request: web.Request, response: web.StreamResponse) -> None:
    response.headers["Server"] = "BackendAI"


def handle_loop_error(
    root_ctx: RootContext,
    loop: asyncio.AbstractEventLoop,
    context: Mapping[str, Any],
) -> None:
    exception = context.get("exception")
    msg = context.get("message", "(empty message)")
    if exception is not None:
        if sys.exc_info()[0] is not None:
            log.exception("Error inside event loop: {0}", msg)
        else:
            exc_info = (type(exception), exception, exception.__traceback__)
            log.error("Error inside event loop: {0}", msg, exc_info=exc_info)


@actxmgr
async def database_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .models.utils import connect_database

    async with connect_database(root_ctx.local_config) as db:
        root_ctx.db = db
        yield


def _init_subapp(
    pkg_name: str,
    root_app: web.Application,
    subapp: web.Application,
    global_middlewares: Iterable[Middleware],
) -> None:
    subapp.on_response_prepare.append(on_prepare)

    async def _set_root_ctx(subapp: web.Application):
        # Allow subapp's access to the root app properties.
        # These are the public APIs exposed to plugins as well.
        subapp["_root.context"] = root_app["_root.context"]

    # We must copy the public interface prior to all user-defined startup signal handlers.
    subapp.on_startup.insert(0, _set_root_ctx)
    if "prefix" not in subapp:
        subapp["prefix"] = pkg_name.split(".")[-1].replace("_", "-")
    prefix = subapp["prefix"]
    root_app.add_subapp("/" + prefix, subapp)
    root_app.middlewares.extend(global_middlewares)


def init_subapp(pkg_name: str, root_app: web.Application, create_subapp: AppCreator) -> None:
    root_ctx: RootContext = root_app["_root.context"]
    subapp, global_middlewares = create_subapp(root_ctx.cors_options)
    _init_subapp(pkg_name, root_app, subapp, global_middlewares)


def build_root_app(
    pidx: int,
    local_config: ServerConfig,
    *,
    cleanup_contexts: Sequence[CleanupContext] | None = None,
    subapp_pkgs: Optional[Sequence[str]] = None,
    scheduler_opts: Optional[Mapping[str, Any]] = None,
) -> web.Application:
    metric_registry = CommonMetricRegistry.instance()
    app = web.Application(
        middlewares=[
            api_middleware,
            exception_middleware,
            build_api_metric_middleware(metric_registry.api),
        ]
    )

    etcd_credentials = None
    if local_config.etcd.user:
        etcd_credentials = {
            "user": local_config.etcd.user,
            "password": local_config.etcd.password,
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
        # TODO: provide a way to specify other scope prefixes
    }
    etcd = AsyncEtcd(
        HostPortPair(host=local_config.etcd.addr.host, port=local_config.etcd.addr.port),
        local_config.etcd.namespace,
        scope_prefix_map,
        credentials=etcd_credentials,
    )
    root_ctx = RootContext()
    root_ctx.etcd = etcd
    root_ctx.local_config = local_config
    root_ctx.pidx = pidx
    root_ctx.cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }
    global_exception_handler = functools.partial(handle_loop_error, root_ctx)
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(global_exception_handler)
    app["_root.context"] = root_ctx
    app.on_response_prepare.append(on_prepare)

    if cleanup_contexts is None:
        cleanup_contexts = [
            database_ctx,
        ]

    async def _cleanup_context_wrapper(cctx, app: web.Application) -> AsyncIterator[None]:
        # aiohttp's cleanup contexts are just async generators, not async context managers.
        cctx_instance = cctx(app["_root.context"])
        app["_cctx_instances"].append(cctx_instance)
        try:
            async with cctx_instance:
                yield
        except Exception as e:
            exc_info = (type(e), e, e.__traceback__)
            log.error("Error initializing cleanup_contexts: {0}", cctx.__name__, exc_info=exc_info)

    async def _call_cleanup_context_shutdown_handlers(app: web.Application) -> None:
        for cctx in app["_cctx_instances"]:
            if hasattr(cctx, "shutdown"):
                try:
                    await cctx.shutdown()
                except Exception:
                    log.exception("error while shutting down a cleanup context")

    app["_cctx_instances"] = []
    app.on_shutdown.append(_call_cleanup_context_shutdown_handlers)
    for cleanup_ctx in cleanup_contexts:
        app.cleanup_ctx.append(
            functools.partial(_cleanup_context_wrapper, cleanup_ctx),
        )
    cors = aiohttp_cors.setup(app, defaults=root_ctx.cors_options)
    # should be done in create_app() in other modules.
    cors.add(app.router.add_route("GET", r"", hello))
    cors.add(app.router.add_route("GET", r"/", hello))
    cors.add(
        app.router.add_route("GET", r"/metrics", build_prometheus_metrics_handler(metric_registry))
    )
    return app


@actxmgr
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: list[Any],
) -> AsyncIterator[None]:
    root_app = build_root_app(pidx, _args[0], subapp_pkgs=global_subapp_pkgs)
    root_ctx: RootContext = root_app["_root.context"]

    local_cfg = cast(ServerConfig, root_ctx.local_config)
    am_cfg = cast(AccountManagerConfig, local_cfg.account_manager)
    Profiler(
        pyroscope_args=PyroscopeArgs(
            enabled=local_cfg.pyroscope.enabled,
            app_name=local_cfg.pyroscope.app_name,
            server_address=local_cfg.pyroscope.server_addr,
            sample_rate=local_cfg.pyroscope.sample_rate,
        )
    )

    # Start aiomonitor.
    # Port is set by config (default=50100 + pidx).
    loop.set_debug(local_cfg.debug.asyncio)
    m = aiomonitor.Monitor(
        loop,
        termui_port=am_cfg.aiomonitor_termui_port + pidx,
        webui_port=am_cfg.aiomonitor_webui_port + pidx,
        console_enabled=False,
        hook_task_factory=local_cfg.debug.enhanced_aiomonitor_task_info,
    )
    m.prompt = f"monitor (manager[{pidx}@{os.getpid()}]) >>> "
    # Add some useful console_locals for ease of debugging
    m.console_locals["root_app"] = root_app
    m.console_locals["root_ctx"] = root_ctx
    aiomon_started = False
    try:
        m.start()
        aiomon_started = True
    except Exception as e:
        log.warning("aiomonitor could not start but skipping this error to continue", exc_info=e)

    # Plugin webapps should be loaded before runner.setup(),
    # which freezes on_startup event.
    try:
        ssl_ctx = None
        if am_cfg.ssl_enabled:
            assert am_cfg.ssl_cert is not None, (
                "Should set `account_manager.ssl-cert` in config file."
            )
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(
                str(am_cfg.ssl_cert),
                str(am_cfg.ssl_privkey),
            )

        runner = web.AppRunner(root_app, keepalive_timeout=30.0)
        await runner.setup()
        service_addr = am_cfg.service_addr
        site = web.TCPSite(
            runner,
            str(service_addr.host),
            service_addr.port,
            backlog=1024,
            reuse_port=True,
            ssl_context=ssl_ctx,
        )
        await site.start()

        if os.geteuid() == 0:
            uid = am_cfg.user
            gid = am_cfg.group
            os.setgroups([
                g.gr_gid for g in grp.getgrall() if pwd.getpwuid(uid).pw_name in g.gr_mem
            ])
            os.setgid(gid)
            os.setuid(uid)
            log.info("changed process uid and gid to {}:{}", uid, gid)
        log.info("started handling API requests at {}", service_addr)

        try:
            yield
        finally:
            log.info("shutting down...")
            await runner.cleanup()
    finally:
        if aiomon_started:
            m.close()


@actxmgr
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: list[Any],
) -> AsyncIterator[None]:
    setproctitle(f"backend.ai: account-manager worker-{pidx}")
    log_endpoint = _args[1]
    logging_config = _args[0].logging
    logger = Logger(
        logging_config,
        is_master=False,
        log_endpoint=log_endpoint,
        msgpack_options={
            "pack_opts": DEFAULT_PACK_OPTS,
            "unpack_opts": DEFAULT_UNPACK_OPTS,
        },
    )
    try:
        with logger:
            async with server_main(loop, pidx, _args):
                yield
    except Exception:
        traceback.print_exc()


@click.group(invoke_without_command=True)
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=Path,
    default=None,
    help="The config file path. (default: ./manager.toml and /etc/backend.ai/manager.toml)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="This option will soon change to --log-level TEXT option.",
)
@click.option(
    "--log-level",
    type=click.Choice([*LogLevel], case_sensitive=False),
    default=LogLevel.INFO,
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    config_path: Path,
    log_level: LogLevel,
    debug: bool = False,
) -> None:
    """
    Start the account-manager service as a foreground process.
    """
    cfg = load_config(config_path, log_level)

    if ctx.invoked_subcommand is None:
        account_manager_cfg = cast(AccountManagerConfig, cfg.account_manager)
        account_manager_cfg.pid_file.touch(exist_ok=True)
        account_manager_cfg.pid_file.write_text(str(os.getpid()))
        ipc_base_path = account_manager_cfg.ipc_base_path
        ipc_base_path.mkdir(exist_ok=True, parents=True)
        log_sockpath = ipc_base_path / f"account-manager-logger-{os.getpid()}.sock"
        log_endpoint = f"ipc://{log_sockpath}"
        logging_config = cfg.logging  # type: ignore[attr-defined]
        try:
            logger = Logger(
                logging_config,
                is_master=True,
                log_endpoint=log_endpoint,
                msgpack_options={
                    "pack_opts": DEFAULT_PACK_OPTS,
                    "unpack_opts": DEFAULT_UNPACK_OPTS,
                },
            )
            with logger:
                setproctitle("backend.ai: account-manager")
                log.info("Backend.AI Account Manager")
                log.info("runtime: {0}", env_info())
                log_config = logging.getLogger("ai.backend.account_manager.config")
                log_config.debug("debug mode enabled.")
                if account_manager_cfg.event_loop == EventLoopType.UVLOOP:
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                try:
                    aiotools.start_server(
                        server_main_logwrapper,
                        num_workers=account_manager_cfg.num_workers,
                        args=(cfg, log_endpoint),
                        wait_timeout=5.0,
                    )
                finally:
                    log.info("terminated.")
        finally:
            if account_manager_cfg.pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                account_manager_cfg.pid_file.unlink()
    else:
        # Click is going to invoke a subcommand.
        pass


if __name__ == "__main__":
    sys.exit(main())
