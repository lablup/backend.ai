from __future__ import annotations

import asyncio
import functools
import grp
import logging
import multiprocessing
import os
import pwd
import signal
import ssl
import sys
import traceback
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Sequence
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from pprint import pformat, pprint
from typing import Any

import aiohttp_cors
import aiomonitor
import aiotools
import click
from aiohttp import web
from aiohttp.typedefs import Middleware
from setproctitle import setproctitle

from ai.backend.common.config import (
    ConfigurationError,
)
from ai.backend.common.defs import (
    NOOP_STORAGE_VOLUME_NAME,
)
from ai.backend.common.dependencies import DependencyBuilderStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.metrics.multiprocess_setup import cleanup_prometheus_multiprocess_dir
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
from ai.backend.common.networking import force_threaded_dns_resolver
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.common.types import HostPortPair as CommonHostPortPair
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel
from ai.backend.logging.otel import OpenTelemetrySpec
from ai.backend.storage.context_types import ArtifactVerifierContext

try:
    import uvloop
except ImportError:
    uvloop = None  # type: ignore[assignment]

from . import __version__ as VERSION
from .api.client import init_client_app
from .api.manager import init_internal_app, init_manager_app
from .config.loaders import load_local_config
from .config.unified import (
    EventLoopType,
    StorageProxyUnifiedConfig,
)
from .context import RootContext
from .dependencies.composer import DependencyInput, StorageDependencyComposer
from .errors import InvalidConfigurationSourceError, InvalidSocketPathError
from .migration import check_latest
from .plugin import (
    StorageClientWebappPluginContext,
    StorageManagerWebappPluginContext,
)
from .volumes.noop import init_noop_volume
from .watcher import main_job

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _is_root() -> bool:
    return os.geteuid() == 0


@dataclass
class ServerMainArgs:
    local_config: StorageProxyUnifiedConfig
    config_path: Path | None
    log_endpoint: str
    log_level: LogLevel


@aiotools.server_context
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    tuple_args: Sequence[Any],
) -> AsyncGenerator[None, signal.Signals]:
    setproctitle(f"backend.ai: storage-proxy worker-{pidx}")
    args = ServerMainArgs(
        local_config=tuple_args[0],
        config_path=tuple_args[1],
        log_endpoint=tuple_args[2],
        log_level=tuple_args[3],
    )
    logger = Logger(
        args.local_config.logging,
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


@asynccontextmanager
async def aiomonitor_ctx(
    local_config: StorageProxyUnifiedConfig,
    pidx: int,
) -> AsyncGenerator[aiomonitor.Monitor]:
    # Port is set by config where the defaults are:
    # termui_port = 38300 + pidx
    # webui_port = 39300 + pidx
    loop = asyncio.get_running_loop()
    m = aiomonitor.Monitor(
        loop,
        termui_port=local_config.storage_proxy.aiomonitor_termui_port + pidx,
        webui_port=local_config.storage_proxy.aiomonitor_webui_port + pidx,
        console_enabled=False,
        hook_task_factory=local_config.debug.enhanced_aiomonitor_task_info,
    )
    Profiler(
        pyroscope_args=PyroscopeArgs(
            enabled=local_config.pyroscope.enabled,
            application_name=local_config.pyroscope.app_name,
            server_address=local_config.pyroscope.server_addr,
            sample_rate=local_config.pyroscope.sample_rate,
        )
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
        yield m
    finally:
        if aiomon_started:
            m.close()


@asynccontextmanager
async def api_ctx(
    local_config: StorageProxyUnifiedConfig,
    etcd: AsyncEtcd,
    root_ctx: RootContext,
) -> AsyncGenerator[tuple[web.Application, web.Application, web.Application]]:
    @asynccontextmanager
    async def _init_storage_webapp_plugin(
        plugin_ctx: BasePluginContext[AbstractPlugin], root_app: web.Application
    ) -> AsyncGenerator[BasePluginContext[AbstractPlugin], None]:
        pid = os.getpid()
        await plugin_ctx.init()
        for plugin_name, plugin_instance in plugin_ctx.plugins.items():
            if pid == 0:
                log.info("Loading storage webapp plugin: {0}", plugin_name)
            subapp, global_middlewares = await plugin_instance.create_app(root_ctx.cors_options)  # type: ignore[attr-defined]
            _init_subapp(plugin_name, root_app, subapp, global_middlewares)
        try:
            yield plugin_ctx
        finally:
            await plugin_ctx.cleanup()

    @asynccontextmanager
    async def client_api_ctx() -> AsyncGenerator[web.Application]:
        client_ssl_ctx = None
        if local_config.api.client.ssl_enabled:
            client_ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            client_ssl_ctx.load_cert_chain(
                str(local_config.api.client.ssl_cert),
                str(local_config.api.client.ssl_privkey),
            )
        client_api_app = await init_client_app(root_ctx)
        client_api_runner = web.AppRunner(client_api_app)
        await client_api_runner.setup()
        client_service_addr = local_config.api.client.service_addr
        client_api_site = web.TCPSite(
            client_api_runner,
            str(client_service_addr.host),
            client_service_addr.port,
            backlog=1024,
            reuse_port=True,
            ssl_context=client_ssl_ctx,
        )
        await client_api_site.start()
        try:
            yield client_api_app
        finally:
            await client_api_runner.cleanup()

    @asynccontextmanager
    async def manager_api_ctx() -> AsyncGenerator[web.Application]:
        manager_ssl_ctx = None
        if local_config.api.manager.ssl_enabled:
            manager_ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            manager_ssl_ctx.load_cert_chain(
                str(local_config.api.manager.ssl_cert),
                str(local_config.api.manager.ssl_privkey),
            )
        manager_api_app = await init_manager_app(root_ctx)
        manager_api_runner = web.AppRunner(manager_api_app)
        await manager_api_runner.setup()
        manager_service_addr_config = local_config.api.manager.service_addr
        manager_service_addr = CommonHostPortPair(
            host=manager_service_addr_config.host,
            port=manager_service_addr_config.port,
        )
        manager_api_site = web.TCPSite(
            manager_api_runner,
            str(manager_service_addr.host),
            manager_service_addr.port,
            backlog=1024,
            reuse_port=True,
            ssl_context=manager_ssl_ctx,
        )
        await manager_api_site.start()
        try:
            yield manager_api_app
        finally:
            await manager_api_runner.cleanup()

    @asynccontextmanager
    async def internal_api_ctx() -> AsyncGenerator[web.Application]:
        internal_api_app = init_internal_app(root_ctx)
        internal_api_runner = web.AppRunner(internal_api_app)
        await internal_api_runner.setup()
        internal_addr = local_config.api.manager.internal_addr
        internal_api_site = web.TCPSite(
            internal_api_runner,
            str(internal_addr.host),
            internal_addr.port,
            backlog=1024,
            reuse_port=True,
        )
        await internal_api_site.start()
        try:
            yield internal_api_app
        finally:
            await internal_api_runner.cleanup()

    async with AsyncExitStack() as api_init_stack:
        client_api_app = await api_init_stack.enter_async_context(client_api_ctx())
        manager_api_app = await api_init_stack.enter_async_context(manager_api_ctx())
        internal_api_app = await api_init_stack.enter_async_context(internal_api_ctx())
        await api_init_stack.enter_async_context(
            _init_storage_webapp_plugin(
                StorageClientWebappPluginContext(etcd, local_config.model_dump()),  # type: ignore[arg-type]
                client_api_app,
            )
        )
        await api_init_stack.enter_async_context(
            _init_storage_webapp_plugin(
                StorageManagerWebappPluginContext(etcd, local_config.model_dump()),  # type: ignore[arg-type]
                manager_api_app,
            )
        )
        try:
            yield client_api_app, manager_api_app, internal_api_app
        finally:
            # volume instances are lazily initialized upon their first usage by the API layers.
            await root_ctx.shutdown_volumes()


async def _on_prepare(_request: web.Request, response: web.StreamResponse) -> None:
    response.headers["Server"] = "BackendAI"


def _init_subapp(
    pkg_name: str,
    root_app: web.Application,
    subapp: web.Application,
    global_middlewares: list[Middleware],
) -> None:
    subapp.on_response_prepare.append(_on_prepare)

    async def _set_root_ctx(subapp: web.Application) -> None:
        # Allow subapp's access to the root app properties.
        # These are the public APIs exposed to plugins as well.
        subapp["ctx"] = root_app["ctx"]

    # We must copy the public interface prior to all user-defined startup signal handlers.
    subapp.on_startup.insert(0, _set_root_ctx)
    if "prefix" not in subapp:
        subapp["prefix"] = pkg_name.split(".")[-1].replace("_", "-")
    prefix = subapp["prefix"]
    root_app.add_subapp("/" + prefix, subapp)
    root_app.middlewares.extend(global_middlewares)


@asynccontextmanager
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    args: ServerMainArgs,
) -> AsyncIterator[None]:
    loop.set_debug(args.local_config.debug.asyncio)

    storage_init_stack = AsyncExitStack()
    await storage_init_stack.__aenter__()
    try:
        monitor = await storage_init_stack.enter_async_context(
            aiomonitor_ctx(args.local_config, pidx)
        )

        dep_stack = DependencyBuilderStack()
        await storage_init_stack.enter_async_context(dep_stack)
        dep_resources = await dep_stack.enter_composer(
            StorageDependencyComposer(),
            DependencyInput(
                config_path=args.config_path,
                pidx=pidx,
                log_level=args.log_level,
            ),
        )

        local_config = dep_resources.bootstrap.config
        etcd = dep_resources.infrastructure.etcd
        event_dispatcher = dep_resources.messaging.event_dispatcher
        event_producer = dep_resources.messaging.event_producer

        root_ctx = RootContext(
            pid=os.getpid(),
            pidx=pidx,
            node_id=local_config.storage_proxy.node_id,
            local_config=local_config,
            etcd=etcd,
            volume_pool=dep_resources.storage.volume_pool,
            storage_pool=dep_resources.storage.storage_pool,
            background_task_manager=dep_resources.storage.background_task_manager,
            event_producer=event_producer,
            event_dispatcher=event_dispatcher,
            watcher=dep_resources.storage.watcher,
            metric_registry=dep_resources.bootstrap.metric_registry,
            cors_options={
                "*": aiohttp_cors.ResourceOptions(  # type: ignore[no-untyped-call]
                    allow_credentials=False, expose_headers="*", allow_headers="*"
                ),
            },
            manager_client_pool=dep_resources.storage.manager_client_pool,
            valkey_artifact_client=dep_resources.infrastructure.valkey.artifact,
            valkey_tus_client=dep_resources.infrastructure.valkey.tus,
            health_probe=dep_resources.system.health_probe,
            volume_stats_observer=dep_resources.storage.volume_stats.observer,
            volume_stats_state=dep_resources.storage.volume_stats.state,
            backends={**dep_resources.plugins.backends},
            volumes={
                NOOP_STORAGE_VOLUME_NAME: init_noop_volume(etcd, event_dispatcher, event_producer)
            },
            artifact_verifier_ctx=ArtifactVerifierContext(),
        )
        await root_ctx.init_storage_artifact_verifier_plugin()
        if pidx == 0:
            await check_latest(root_ctx)

        if local_config.otel.enabled:
            meta = dep_resources.system.service_discovery.sd_loop.metadata
            otel_spec = OpenTelemetrySpec(
                service_name=meta.service_group,
                service_version=meta.version,
                log_level=local_config.otel.log_level,
                endpoint=local_config.otel.endpoint,
                service_instance_id=meta.id,
                service_instance_name=meta.display_name,
                max_queue_size=local_config.otel.max_queue_size,
                max_export_batch_size=local_config.otel.max_export_batch_size,
            )
            BraceStyleAdapter.apply_otel(otel_spec)

        (
            client_api_app,
            manager_api_app,
            internal_api_app,
        ) = await storage_init_stack.enter_async_context(api_ctx(local_config, etcd, root_ctx))
        monitor.console_locals["root_ctx"] = root_ctx
        monitor.console_locals["client_api_app"] = client_api_app
        monitor.console_locals["manager_api_app"] = manager_api_app
        monitor.console_locals["internal_api_app"] = internal_api_app

        if _is_root():
            uid = local_config.storage_proxy.user
            gid = local_config.storage_proxy.group
            if uid is not None and gid is not None:
                os.setgroups(
                    [g.gr_gid for g in grp.getgrall() if pwd.getpwuid(uid).pw_name in g.gr_mem],
                )
                os.setgid(gid)
                os.setuid(uid)
            log.info("Changed process uid:gid to {}:{}", uid, gid)

        log.info("Started the storage-proxy service.")
    except Exception:
        log.exception("Server initialization failure; triggering shutdown...")
        loop.call_later(0.2, os.kill, 0, signal.SIGINT)
    try:
        yield
    finally:
        log.info("Shutting down...")
        await storage_init_stack.__aexit__(None, None, None)


@click.group(invoke_without_command=True)
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help=(
        "The config file path. "
        "(default: ./storage-proxy.toml and /etc/backend.ai/storage-proxy.toml)"
    ),
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
    cli_ctx: click.Context,
    config_path: Path,
    log_level: LogLevel,
    debug: bool = False,
) -> int:
    """Start the storage-proxy service as a foreground process."""
    force_threaded_dns_resolver()
    log_level = LogLevel.DEBUG if debug else log_level
    resolved_config_path = config_path.resolve() if config_path is not None else None
    try:
        local_config = load_local_config(resolved_config_path, log_level=log_level)
    except ConfigurationError as e:
        print(
            "ConfigurationError: Could not read or validate the storage-proxy local config:",
            file=sys.stderr,
        )
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort() from e
    # Note: logging configuration is handled separately in Logger class
    # Debug mode is already set during config loading if needed

    multiprocessing.set_start_method("spawn")

    if cli_ctx.invoked_subcommand is None:
        local_config.storage_proxy.pid_file.write_text(str(os.getpid()))
        ipc_base_path = local_config.storage_proxy.ipc_base_path
        log_sockpath = Path(
            ipc_base_path / f"storage-proxy-logger-{os.getpid()}.sock",
        )
        log_sockpath.parent.mkdir(parents=True, exist_ok=True)
        log_endpoint = f"ipc://{log_sockpath}"
        try:
            logger = Logger(
                local_config.logging,
                is_master=True,
                log_endpoint=log_endpoint,
                msgpack_options={
                    "pack_opts": DEFAULT_PACK_OPTS,
                    "unpack_opts": DEFAULT_UNPACK_OPTS,
                },
            )
            with logger:
                setproctitle("backend.ai: storage-proxy")
                log.info("Backend.AI Storage Proxy", VERSION)
                log.info("Runtime: {0}", env_info())
                log.info("Node ID: {0}", local_config.storage_proxy.node_id)
                log_config = logging.getLogger("ai.backend.agent.config")
                if local_config.debug.enabled:
                    log_config.debug("debug mode enabled.")
                if local_config.debug.enabled:
                    print("== Storage proxy configuration ==")
                    pprint(local_config.model_dump())
                runner: Callable[..., Any]
                match local_config.storage_proxy.event_loop:
                    case EventLoopType.UVLOOP:
                        if uvloop is None:
                            raise ImportError(
                                "uvloop is not installed. Install it with: pip install uvloop"
                            )
                        runner = uvloop.run
                        log.info("Using uvloop as the event loop backend")
                    case EventLoopType.ASYNCIO:
                        runner = asyncio.run
                insock_path_prefix = local_config.storage_proxy.watcher_insock_path_prefix
                outsock_path_prefix = local_config.storage_proxy.watcher_outsock_path_prefix
                num_workers = local_config.storage_proxy.num_proc

                if local_config.storage_proxy.use_watcher:
                    if not _is_root():
                        raise InvalidConfigurationSourceError(
                            "Storage proxy must be run as root if watcher is enabled. Else, set"
                            " `use-watcher` to false in your local config file."
                        )
                    insock_path: str | None = local_config.storage_proxy.watcher_insock_path_prefix
                    outsock_path: str | None = (
                        local_config.storage_proxy.watcher_outsock_path_prefix
                    )
                    if insock_path is None or outsock_path is None:
                        raise InvalidSocketPathError(
                            "Socket path must be not null. Please set valid socket path to"
                            " `watcher-insock-path-prefix` and `watcher-outsock-path-prefix` in"
                            " your local config file."
                        )
                    extra_procs = tuple(
                        functools.partial(
                            main_job, worker_pidx, insock_path_prefix, outsock_path_prefix
                        )
                        for worker_pidx in range(num_workers)
                    )
                else:
                    extra_procs = tuple()

                try:
                    aiotools.start_server(
                        server_main_logwrapper,
                        num_workers=num_workers,
                        extra_procs=extra_procs,
                        args=(local_config, resolved_config_path, log_endpoint, log_level),
                        runner=runner,
                    )
                finally:
                    cleanup_prometheus_multiprocess_dir()
                log.info("exit.")
        finally:
            if local_config.storage_proxy.pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                local_config.storage_proxy.pid_file.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
