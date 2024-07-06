import asyncio
import functools
import grp
import importlib
import importlib.resources
import logging
import os
import pwd
import sys
import traceback
import uuid
from contextlib import asynccontextmanager as actxmgr
from logging import LoggerAdapter
from pathlib import Path
from typing import Any, AsyncIterator, Final, Iterable, Mapping, Sequence, cast

import aiohttp_cors
import aiohttp_jinja2
import aiomonitor
import aiotools
import click
import jinja2
from aiohttp import web
from setproctitle import setproctitle

from ai.backend.common.logging import BraceStyleAdapter, Logger
from ai.backend.common.types import LogSeverity
from ai.backend.common.utils import env_info
from ai.backend.wsproxy.exceptions import (
    BackendError,
    GenericBadRequest,
    InternalServerError,
    MethodNotAllowed,
    URLNotFound,
)
from ai.backend.wsproxy.types import (
    AppCreator,
    ProxyProtocol,
    WebMiddleware,
    WebRequestHandler,
)

from . import __version__
from .config import ServerConfig
from .config import load as load_config
from .defs import CleanupContext, RootContext
from .proxy.frontend import (
    HTTPPortFrontend,
    TCPFrontend,
)
from .utils import (
    config_key_to_kebab_case,
    ensure_json_serializable,
    mime_match,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

REDIS_APPPROXY_DB: Final[int] = 10  # FIXME: move to ai.backend.common.defs
EVENT_DISPATCHER_CONSUMER_GROUP: Final[str] = "appwsproxy"

global_subapp_pkgs: Final[list[str]] = [
    ".circuit",
    ".conf",
    ".endpoint",
    ".proxy",
    ".setup",
]


@web.middleware
async def request_context_aware_middleware(
    request: web.Request, handler: WebRequestHandler
) -> web.StreamResponse:
    request_id = request.headers.get("X-BackendAI-RequestID", str(uuid.uuid4()))
    request["request_id"] = request_id
    request["log"] = BraceStyleAdapter(logging.getLogger(f"{__spec__.name} - #{request_id}"))  # type: ignore[name-defined]
    resp = await handler(request)
    return resp


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
            log.exception("Internal server error raised inside handlers")
        if mime_match(request.headers.get("accept", "text/html"), "application/json", strict=True):
            return web.json_response(
                ensure_json_serializable(ex.body_dict),
                status=ex.status_code,
            )
        else:
            return aiohttp_jinja2.render_template(
                "error.jinja2",
                request,
                ex.body_dict,
            )
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


@actxmgr
async def proxy_frontend_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    match root_ctx.local_config.wsproxy.protocol:
        case ProxyProtocol.HTTP:
            root_ctx.proxy_frontend = HTTPPortFrontend(root_ctx)
        case ProxyProtocol.TCP:
            root_ctx.proxy_frontend = TCPFrontend(root_ctx)
        case _:
            log.error("Unsupported protocol {}", root_ctx.local_config.wsproxy.protocol)
    await root_ctx.proxy_frontend.start()
    log.debug("started proxy protocol {}", root_ctx.proxy_frontend.__class__.__name__)
    yield
    await root_ctx.proxy_frontend.terminate_all_circuits()
    await root_ctx.proxy_frontend.stop()


async def hello(request: web.Request) -> web.Response:
    """
    Returns the API version number.
    """
    return web.json_response({
        "wsproxy": __version__,
    })


async def status(request: web.Request) -> web.Response:
    request["do_not_print_access_log"] = True
    return web.json_response({"api_version": "v2"})


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


def _init_subapp(
    pkg_name: str,
    root_app: web.Application,
    subapp: web.Application,
    global_middlewares: Iterable[WebMiddleware],
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
    subapp_pkgs: Sequence[str] = [],
) -> web.Application:
    app = web.Application(
        middlewares=[
            request_context_aware_middleware,
            exception_middleware,
            api_middleware,
        ]
    )
    root_ctx = RootContext()
    global_exception_handler = functools.partial(handle_loop_error, root_ctx)
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(global_exception_handler)
    app["_root.context"] = root_ctx
    root_ctx.local_config = local_config
    root_ctx.pidx = pidx
    root_ctx.cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }
    app.on_response_prepare.append(on_prepare)

    with importlib.resources.as_file(importlib.resources.files("ai.backend.wsproxy")) as f:
        template_path = f / "templates"
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_path))

    if cleanup_contexts is None:
        cleanup_contexts = [
            proxy_frontend_ctx,
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
    cors.add(app.router.add_route("GET", "/status", status))
    if subapp_pkgs is None:
        subapp_pkgs = []
    for pkg_name in subapp_pkgs:
        if pidx == 0:
            log.info("Loading module: {0}", pkg_name[1:])
        subapp_mod = importlib.import_module(pkg_name, "ai.backend.wsproxy.api")
        init_subapp(pkg_name, app, getattr(subapp_mod, "create_app"))
    return app


@actxmgr
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: tuple[ServerConfig, str],
) -> AsyncIterator[None]:
    root_app = build_root_app(pidx, _args[0], subapp_pkgs=global_subapp_pkgs)
    root_ctx: RootContext = root_app["_root.context"]

    # Start aiomonitor.
    # Port is set by config (default=50100 + pidx).
    loop.set_debug(root_ctx.local_config.debug.asyncio)
    m = aiomonitor.Monitor(
        loop,
        termui_port=root_ctx.local_config.wsproxy.aiomonitor_termui_port + pidx,
        webui_port=root_ctx.local_config.wsproxy.aiomonitor_webui_port + pidx,
        console_enabled=False,
        hook_task_factory=root_ctx.local_config.debug.enhanced_aiomonitor_task_info,
    )
    m.prompt = f"monitor (wsproxy[{pidx}@{os.getpid()}]) >>> "
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
        runner = web.AppRunner(root_app, keepalive_timeout=30.0)
        await runner.setup()
        site = web.TCPSite(
            runner,
            str(root_ctx.local_config.wsproxy.bind_host),
            root_ctx.local_config.wsproxy.bind_api_port,
            backlog=1024,
            reuse_port=True,
        )
        await site.start()

        if os.geteuid() == 0:
            uid = root_ctx.local_config.wsproxy.user
            gid = root_ctx.local_config.wsproxy.group
            os.setgroups([
                g.gr_gid for g in grp.getgrall() if pwd.getpwuid(uid).pw_name in g.gr_mem
            ])
            os.setgid(gid)
            os.setuid(uid)
            log.info("changed process uid and gid to {}:{}", uid, gid)
        log.info(
            "started handling API requests at {}:{}",
            root_ctx.local_config.wsproxy.bind_host,
            root_ctx.local_config.wsproxy.bind_api_port,
        )

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
    _args: tuple[ServerConfig, str],
) -> AsyncIterator[None]:
    setproctitle(f"backend.ai: wsproxy worker-{pidx}")
    log_endpoint = _args[1]
    logging_config = config_key_to_kebab_case(_args[0].logging.model_dump(exclude_none=True))
    logging_config["endpoint"] = log_endpoint
    logger = Logger(logging_config, is_master=False, log_endpoint=log_endpoint)
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
    help=("The config file path. (default: ./wsproxy.toml and /etc/backend.ai/wsproxy.toml)"),
)
@click.option(
    "--log-level",
    type=click.Choice([*LogSeverity.__members__.keys()], case_sensitive=False),
    default="INFO",
    help="Set the logging verbosity level",
)
@click.pass_context
def main(ctx: click.Context, config_path: Path, log_level: str) -> None:
    """
    Start the wsproxy service as a foreground process.
    """
    cfg = load_config(config_path, log_level)

    if ctx.invoked_subcommand is None:
        cfg.wsproxy.pid_file.touch(exist_ok=True)
        cfg.wsproxy.pid_file.write_text(str(os.getpid()))
        ipc_base_path = cfg.wsproxy.ipc_base_path
        ipc_base_path.mkdir(exist_ok=True, parents=True)
        log_sockpath = ipc_base_path / f"worker-logger-{os.getpid()}.sock"
        log_endpoint = f"ipc://{log_sockpath}"
        logging_config = config_key_to_kebab_case(cfg.logging.model_dump(exclude_none=True))
        logging_config["endpoint"] = log_endpoint
        try:
            logger = Logger(logging_config, is_master=True, log_endpoint=log_endpoint)
            with logger:
                setproctitle("backend.ai: wsproxy")
                log.info("Backend.AI WSProxy {0}", __version__)
                log.info("runtime: {0}", env_info())
                log_config = logging.getLogger("ai.backend.wsproxy.config")
                log_config.debug("debug mode enabled.")
                if cfg.wsproxy.event_loop == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                try:
                    aiotools.start_server(
                        server_main_logwrapper,
                        num_workers=1,
                        args=(cfg, log_endpoint),
                        wait_timeout=5.0,
                    )
                finally:
                    log.info("terminated.")
        finally:
            if cfg.wsproxy.pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                cfg.wsproxy.pid_file.unlink()
    else:
        # Click is going to invoke a subcommand.
        pass


if __name__ == "__main__":
    sys.exit(main())
