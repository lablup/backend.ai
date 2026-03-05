from __future__ import annotations

import asyncio
import functools
import grp
import logging
import os
import pwd
import signal
import ssl
import sys
import traceback
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Callable,
    Iterable,
    Mapping,
    Sequence,
)
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import (
    Any,
    Final,
)

import aiomonitor
import aiotools
import click
import uvloop
from aiohttp import web
from aiohttp.typedefs import Handler, Middleware
from opentelemetry.instrumentation.aiohttp_server import (
    middleware as otel_server_middleware,
)
from setproctitle import setproctitle

from ai.backend.common.cli import LazyGroup
from ai.backend.common.config import find_config_file
from ai.backend.common.dependencies import DependencyBuilderStack
from ai.backend.common.json import dump_json_str
from ai.backend.common.metrics.http import build_prometheus_metrics_handler
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.metrics.multiprocess import cleanup_prometheus_multiprocess_dir
from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel
from ai.backend.logging.otel import (
    instrument_aiohttp_client,
    instrument_aiohttp_server,
)

from . import __version__
from .api import ManagerStatus
from .api.rest.middleware import (
    build_auth_middleware,
    build_exception_middleware,
)
from .config.bootstrap import BootstrapConfig
from .config.unified import EventLoopType
from .dependencies import DependencyInput, DependencyResources, ManagerDependencyComposer
from .plugin.webapp import WebappPluginContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

EVENT_DISPATCHER_CONSUMER_GROUP: Final = "manager"


@asynccontextmanager
async def webapp_plugin_ctx(
    root_app: web.Application,
    *,
    dep_resources: DependencyResources,
    pidx: int,
) -> AsyncIterator[None]:
    r = dep_resources
    plugin_ctx = WebappPluginContext(
        r.bootstrap.etcd,
        r.bootstrap.config_provider.config.model_dump(by_alias=True),
    )
    await plugin_ctx.init(
        context=None,
        allowlist=r.bootstrap.config_provider.config.manager.allowed_plugins,
        blocklist=r.bootstrap.config_provider.config.manager.disabled_plugins,
    )
    cors_options = r.system.cors_options
    for plugin_name, plugin_instance in plugin_ctx.plugins.items():
        if pidx == 0:
            log.info("Loading webapp plugin: {0}", plugin_name)
        subapp, global_middlewares = await plugin_instance.create_app(cors_options)
        _init_subapp(plugin_name, root_app, subapp, global_middlewares)
    try:
        yield
    finally:
        await plugin_ctx.cleanup()


@asynccontextmanager
async def manager_status_ctx(
    pidx: int,
    config_provider: Any,
) -> AsyncIterator[None]:
    if pidx == 0:
        mgr_status = await config_provider.legacy_etcd_config_loader.get_manager_status()
        if mgr_status is None or mgr_status not in (ManagerStatus.RUNNING, ManagerStatus.FROZEN):
            # legacy transition: we now have only RUNNING or FROZEN for HA setup.
            await config_provider.legacy_etcd_config_loader.update_manager_status(
                ManagerStatus.RUNNING
            )
            mgr_status = ManagerStatus.RUNNING
        log.info("Manager status: {}", mgr_status)
        tz = config_provider.config.system.timezone
        log.info("Configured timezone: {}", tz.tzname(datetime.now(UTC)))
    yield


_error_monitor_ref: Any = None


def handle_loop_error(
    loop: asyncio.AbstractEventLoop,
    context: Mapping[str, Any],
) -> None:
    exception = context.get("exception")
    msg = context.get("message", "(empty message)")
    if exception is not None:
        if sys.exc_info()[0] is not None:
            log.exception("Error inside event loop: {0}", msg)
            if _error_monitor_ref is not None:
                loop.create_task(_error_monitor_ref.capture_exception())
        else:
            exc_info = (type(exception), exception, exception.__traceback__)
            log.error("Error inside event loop: {0}", msg, exc_info=exc_info)
            if _error_monitor_ref is not None:
                loop.create_task(_error_monitor_ref.capture_exception(exc_instance=exception))


def _init_subapp(
    pkg_name: str,
    root_app: web.Application,
    subapp: web.Application,
    global_middlewares: Iterable[Middleware],
) -> None:
    from .api.rest.app import on_prepare

    subapp.on_response_prepare.append(on_prepare)

    async def _set_root_app(subapp: web.Application) -> None:
        subapp["_root_app"] = root_app

    # We must copy the public interface prior to all user-defined startup signal handlers.
    subapp.on_startup.insert(0, _set_root_app)
    if "prefix" not in subapp:
        subapp["prefix"] = pkg_name.split(".")[-1].replace("_", "-")
    prefix = subapp["prefix"]
    root_app.add_subapp("/" + prefix, subapp)
    root_app.middlewares.extend(global_middlewares)


def build_prometheus_service_discovery_handler(
    service_discovery: Any,
) -> Handler:
    async def _handler(_request: web.Request) -> web.Response:
        services = await service_discovery.discover()
        resp = []
        for service in services:
            resp.append({
                "targets": [f"{service.endpoint.prometheus_address}"],
                "labels": {
                    **service.labels,
                    "service_id": service.id,
                    "service_group": service.service_group,
                    "display_name": service.display_name,
                    "version": service.version,
                },
            })

        return web.json_response(
            resp,
            status=200,
            dumps=dump_json_str,
        )

    return _handler


def build_internal_app(dep_resources: DependencyResources) -> web.Application:
    app = web.Application()
    metric_registry = CommonMetricRegistry.instance()
    app.router.add_route("GET", r"/metrics", build_prometheus_metrics_handler(metric_registry))
    app.router.add_route(
        "GET",
        r"/metrics/service_discovery",
        build_prometheus_service_discovery_handler(dep_resources.system.service_discovery),
    )
    return app


@dataclass
class ServerMainArgs:
    bootstrap_cfg: BootstrapConfig
    bootstrap_cfg_path: Path
    log_endpoint: str
    log_level: LogLevel


@asynccontextmanager
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    args: ServerMainArgs,
) -> AsyncIterator[None]:
    boostrap_config = args.bootstrap_cfg
    loop.set_debug(boostrap_config.debug.asyncio)
    manager_init_stack = AsyncExitStack()

    @asynccontextmanager
    async def aiomonitor_ctx() -> AsyncIterator[aiomonitor.Monitor]:
        # Port is set by config where the defaults are:
        # termui_port = 38100 + pidx
        # webui_port = 39100 + pidx
        m = aiomonitor.Monitor(
            loop,
            termui_port=boostrap_config.manager.aiomonitor_termui_port + pidx,
            webui_port=boostrap_config.manager.aiomonitor_webui_port + pidx,
            console_enabled=False,
            hook_task_factory=boostrap_config.debug.enhanced_aiomonitor_task_info,
        )
        m.prompt = f"monitor (manager[{pidx}@{os.getpid()}]) >>> "
        m.console_locals["root_app"] = root_app
        aiomon_started = False
        try:
            m.start()
            aiomon_started = True
        except Exception as e:
            log.warning(
                "aiomonitor could not start but skipping this error to continue",
                exc_info=e,
            )
        try:
            yield m
        finally:
            if aiomon_started:
                m.close()

    @asynccontextmanager
    async def webapp_ctx(
        root_app: web.Application,
        dep_resources: DependencyResources,
    ) -> AsyncGenerator[None]:
        config_provider = dep_resources.bootstrap.config_provider

        runner = web.AppRunner(root_app, keepalive_timeout=30.0)

        internal_app = build_internal_app(dep_resources)
        internal_runner = web.AppRunner(internal_app, keepalive_timeout=30.0)

        ssl_ctx = None
        if config_provider.config.manager.ssl_enabled:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(
                str(config_provider.config.manager.ssl_cert),
                config_provider.config.manager.ssl_privkey,
            )
        await runner.setup()  # The cleanup context initialization happens here.
        await internal_runner.setup()
        service_addr = config_provider.config.manager.service_addr
        internal_addr = config_provider.config.manager.internal_addr
        site = web.TCPSite(
            runner,
            service_addr.host,
            service_addr.port,
            backlog=1024,
            reuse_port=True,
            ssl_context=ssl_ctx,
        )
        internal_site = web.TCPSite(
            internal_runner,
            internal_addr.host,
            internal_addr.port,
            backlog=1024,
            reuse_port=True,
        )
        await site.start()
        await internal_site.start()
        log.info(
            "started handling API requests at {}",
            service_addr,
        )

        try:
            yield
        finally:
            await runner.cleanup()

    await manager_init_stack.__aenter__()
    try:
        from .api.rest.app import build_root_app

        root_app = build_root_app(
            pidx,
            boostrap_config,
            loop_error_handler=functools.partial(handle_loop_error),
        )

        await manager_init_stack.enter_async_context(aiomonitor_ctx())

        # Initialize all dependencies via the Composer (replaces individual cleanup contexts)
        dep_stack = DependencyBuilderStack()
        await manager_init_stack.enter_async_context(dep_stack)
        dep_input = DependencyInput(
            config_path=args.bootstrap_cfg_path,
            pidx=pidx,
            log_level=args.log_level,
        )
        dep_resources = await dep_stack.enter_composer(
            ManagerDependencyComposer(),
            dep_input,
        )

        # Set the error monitor reference for the event loop error handler
        global _error_monitor_ref
        _error_monitor_ref = dep_resources.monitoring.error_monitor

        # Insert DI-based middlewares now that dependencies are available.
        # Maintain order: request_id(0) → exception(1) → auth(2) → api → metric
        root_app.middlewares.insert(
            1,
            build_exception_middleware(
                error_monitor=dep_resources.monitoring.error_monitor,
                stats_monitor=dep_resources.monitoring.stats_monitor,
                config_provider=dep_resources.bootstrap.config_provider,
            ),
        )
        root_app.middlewares.insert(
            2,
            build_auth_middleware(
                db=dep_resources.infrastructure.db,
                jwt_validator=dep_resources.system.jwt_validator,
                valkey_stat=dep_resources.infrastructure.valkey.stat,
                hook_plugin_ctx=dep_resources.plugins.hook_plugin_ctx,
            ),
        )

        # Build and mount the API module tree.
        # Must happen before runner.setup() which freezes the application router.
        from .api.rest.setup import setup_api

        setup_api(root_app, dep_resources, pidx)

        # Manager status check
        config_provider = dep_resources.bootstrap.config_provider
        await manager_init_stack.enter_async_context(manager_status_ctx(pidx, config_provider))

        # TODO: Remove manual middleware injection once the manager startup is
        # decoupled from the aiohttp Application lifecycle. Currently root_app is
        # instantiated before OTel config is available, so instrument_aiohttp_server()
        # (which patches the class via setattr) cannot take effect automatically.
        if config_provider.config.otel.enabled:
            instrument_aiohttp_server()
            instrument_aiohttp_client()
            root_app.middlewares.insert(0, otel_server_middleware)

        # Plugin webapps should be loaded before runner.setup() because root_app is frozen upon on_startup event.
        await manager_init_stack.enter_async_context(
            webapp_plugin_ctx(root_app, dep_resources=dep_resources, pidx=pidx)
        )
        await manager_init_stack.enter_async_context(webapp_ctx(root_app, dep_resources))

        if os.geteuid() == 0:
            uid = config_provider.config.manager.user
            gid = config_provider.config.manager.group
            if uid is None or gid is None:
                raise ValueError("user/group must be specified when running as root")

            os.setgroups([
                g.gr_gid for g in grp.getgrall() if pwd.getpwuid(uid).pw_name in g.gr_mem
            ])
            os.setgid(gid)
            os.setuid(uid)
            log.info("changed process uid and gid to {}:{}", uid, gid)

        log.info("Started the manager service.")
    except Exception:
        log.exception("Server initialization failure; triggering shutdown...")
        loop.call_later(0.2, os.kill, 0, signal.SIGINT)

    try:
        yield
    finally:
        _error_monitor_ref = None
        log.info("shutting down...")
        await manager_init_stack.__aexit__(None, None, None)


@aiotools.server_context
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    tuple_args: Sequence[Any],
) -> AsyncGenerator[None, signal.Signals]:
    setproctitle(f"backend.ai: manager worker-{pidx}")
    args = ServerMainArgs(
        bootstrap_cfg=tuple_args[0],
        bootstrap_cfg_path=tuple_args[1],
        log_endpoint=tuple_args[2],
        log_level=tuple_args[3],
    )
    logger = Logger(
        args.bootstrap_cfg.logging,
        is_master=False,
        log_endpoint=args.log_endpoint,
        msgpack_options={
            "pack_opts": DEFAULT_PACK_OPTS,
            "unpack_opts": DEFAULT_UNPACK_OPTS,
        },
    )
    try:
        with logger:
            async with server_main(loop, pidx, args):
                yield
    except Exception:
        traceback.print_exc(file=sys.stderr)


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
    help="A shortcut to set `--log-level=DEBUG`",
)
@click.option(
    "--log-level",
    type=click.Choice([*LogLevel], case_sensitive=False),
    default=LogLevel.NOTSET,
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    config_path: Path | None,
    debug: bool,
    log_level: LogLevel,
) -> None:
    """
    Start the manager service as a foreground process.
    """
    log_level = LogLevel.DEBUG if debug else log_level

    if config_path is None:
        discovered_cfg_path = find_config_file("manager")
    else:
        discovered_cfg_path = Path(config_path)

    bootstrap_cfg = asyncio.run(BootstrapConfig.load_from_file(discovered_cfg_path, log_level))

    if ctx.invoked_subcommand is None:
        bootstrap_cfg.manager.pid_file.write_text(str(os.getpid()))
        ipc_base_path = bootstrap_cfg.manager.ipc_base_path
        log_sockpath = ipc_base_path / f"manager-logger-{os.getpid()}.sock"
        log_endpoint = f"ipc://{log_sockpath}"
        try:
            logger = Logger(
                bootstrap_cfg.logging,
                is_master=True,
                log_endpoint=log_endpoint,
                msgpack_options={
                    "pack_opts": DEFAULT_PACK_OPTS,
                    "unpack_opts": DEFAULT_UNPACK_OPTS,
                },
            )
            with logger:
                ns = bootstrap_cfg.etcd.namespace
                setproctitle(f"backend.ai: manager {ns}")
                log.info("Backend.AI Manager {0}", __version__)
                log.info("runtime: {0}", env_info())
                log_config = logging.getLogger("ai.backend.manager.config")
                log_config.debug("debug mode enabled.")
                runner: Callable[..., Any]
                match bootstrap_cfg.manager.event_loop:
                    case EventLoopType.UVLOOP:
                        runner = uvloop.run
                        log.info("Using uvloop as the event loop backend")
                    case EventLoopType.ASYNCIO:
                        runner = asyncio.run
                try:
                    aiotools.start_server(
                        server_main_logwrapper,
                        num_workers=bootstrap_cfg.manager.num_proc,
                        args=(bootstrap_cfg, discovered_cfg_path, log_endpoint, log_level),
                        wait_timeout=5.0,
                        runner=runner,
                    )
                finally:
                    cleanup_prometheus_multiprocess_dir()
                    log.info("terminated.")
        finally:
            if bootstrap_cfg.manager.pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                bootstrap_cfg.manager.pid_file.unlink()
    else:
        # Click is going to invoke a subcommand.
        pass


@main.group(cls=LazyGroup, import_name="ai.backend.manager.api.auth:cli")
def auth() -> None:
    pass


if __name__ == "__main__":
    sys.exit(main())
