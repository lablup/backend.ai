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
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from pprint import pformat, pprint
from typing import TYPE_CHECKING, Any, AsyncGenerator, AsyncIterator, Sequence

import aiohttp_cors
import aiomonitor
import aiotools
import click
from aiohttp import web
from aiohttp.typedefs import Middleware
from setproctitle import setproctitle

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.config import (
    ConfigurationError,
)
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.defs import (
    NOOP_STORAGE_VOLUME_NAME,
    REDIS_BGTASK_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
    RedisRole,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.health_checker.checkers.etcd import EtcdHealthChecker
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.health_checker.probe import HealthProbe, HealthProbeOptions
from ai.backend.common.health_checker.types import ComponentId
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
from ai.backend.common.plugin import BasePluginContext
from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
    ETCDServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.redis_discovery.service_discovery import (
    RedisServiceDiscovery,
    RedisServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscovery,
    ServiceDiscoveryLoop,
    ServiceEndpoint,
    ServiceMetadata,
)
from ai.backend.common.types import (
    AGENTID_STORAGE,
    RedisProfileTarget,
    ServiceDiscoveryType,
    safe_print_redis_config,
)
from ai.backend.common.types import HostPortPair as CommonHostPortPair
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel
from ai.backend.logging.otel import OpenTelemetrySpec
from ai.backend.storage.context_types import ArtifactVerifierContext

from . import __version__ as VERSION
from .client.manager import ManagerHTTPClientPool
from .config.loaders import load_local_config, make_etcd
from .config.unified import (
    EventLoopType,
    LegacyReservoirConfig,
    ReservoirConfig,
    StorageProxyUnifiedConfig,
)
from .errors import InvalidConfigurationSourceError, InvalidSocketPathError
from .watcher import WatcherClient

if TYPE_CHECKING:
    from .context import RootContext
    from .volumes.pool import VolumePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _is_root() -> bool:
    return os.geteuid() == 0


@aiotools.server_context
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Sequence[Any],
) -> AsyncGenerator[None, signal.Signals]:
    setproctitle(f"backend.ai: storage-proxy worker-{pidx}")
    local_config: StorageProxyUnifiedConfig = _args[0]
    log_endpoint = _args[1]
    logger = Logger(
        local_config.logging,
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
async def etcd_ctx(local_config: StorageProxyUnifiedConfig) -> AsyncGenerator[AsyncEtcd]:
    etcd = make_etcd(local_config)
    try:
        yield etcd
    finally:
        await etcd.close()


@asynccontextmanager
async def redis_ctx(etcd: AsyncEtcd, pidx: int) -> AsyncGenerator[RedisConfig]:
    raw_redis_config = await etcd.get_prefix("config/redis")
    redis_config = RedisConfig.model_validate(raw_redis_config)
    log.info(
        "PID: {0} - configured redis_config: {1}",
        pidx,
        safe_print_redis_config(redis_config),
    )
    yield redis_config


@asynccontextmanager
async def bgtask_ctx(
    local_config: StorageProxyUnifiedConfig,
    redis_config: RedisConfig,
    event_producer: EventProducer,
    volume_pool: VolumePool,
) -> AsyncGenerator[BackgroundTaskManager]:
    from .bgtask.registry import BgtaskHandlerRegistryCreator

    redis_profile_target = redis_config.to_redis_profile_target()
    valkey_client = await ValkeyBgtaskClient.create(
        redis_profile_target.profile_target(RedisRole.BGTASK).to_valkey_target(),
        human_readable_name="storage_bgtask",
        db_id=REDIS_BGTASK_DB,
    )
    bgtask_registry_creator = BgtaskHandlerRegistryCreator(volume_pool, event_producer)
    registry = bgtask_registry_creator.create()
    bgtask_mgr = BackgroundTaskManager(
        event_producer=event_producer,
        task_registry=registry,
        valkey_client=valkey_client,
        server_id=local_config.storage_proxy.node_id,
    )

    try:
        yield bgtask_mgr
    finally:
        await valkey_client.close()


async def _make_message_queue(
    local_config: StorageProxyUnifiedConfig,
    redis_profile_target: RedisProfileTarget,
) -> AbstractMessageQueue:
    from .context import EVENT_DISPATCHER_CONSUMER_GROUP

    stream_redis_target = redis_profile_target.profile_target(RedisRole.STREAM)
    node_id = local_config.storage_proxy.node_id
    args = RedisMQArgs(
        anycast_stream_key="events",
        broadcast_channel="events_all",
        consume_stream_keys=None,
        subscribe_channels={
            "events_all",
        },
        group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
        node_id=node_id,
        db=REDIS_STREAM_DB,
    )
    if local_config.storage_proxy.use_experimental_redis_event_dispatcher:
        return HiRedisQueue(
            stream_redis_target,
            args,
        )
    return await RedisQueue.create(
        redis_profile_target.profile_target(RedisRole.STREAM),
        args,
    )


@asynccontextmanager
async def event_ctx(
    local_config: StorageProxyUnifiedConfig,
    redis_config: RedisConfig,
    pidx: int,
    metric_registry: CommonMetricRegistry,
) -> AsyncGenerator[tuple[EventDispatcher, EventProducer]]:
    redis_profile_target = redis_config.to_redis_profile_target()
    mq = await _make_message_queue(
        local_config,
        redis_profile_target,
    )
    event_producer = EventProducer(
        mq,
        source=AGENTID_STORAGE,
        log_events=local_config.debug.log_events,
    )
    log.info(
        "PID: {0} - Event producer created. (redis_config: {1})",
        pidx,
        safe_print_redis_config(redis_config),
    )
    event_dispatcher = EventDispatcher(
        mq,
        log_events=local_config.debug.log_events,
        event_observer=metric_registry.event,
    )
    log.info(
        "PID: {0} - Event dispatcher created. (redis_config: {1})",
        pidx,
        safe_print_redis_config(redis_config),
    )
    await event_dispatcher.start()
    try:
        yield event_dispatcher, event_producer
    finally:
        await event_producer.close()
        await event_dispatcher.close()


@asynccontextmanager
async def watcher_ctx(
    local_config: StorageProxyUnifiedConfig,
    pidx: int,
) -> AsyncGenerator[WatcherClient | None]:
    if local_config.storage_proxy.use_watcher:
        if not _is_root():
            raise InvalidConfigurationSourceError(
                "Storage proxy must be run as root if watcher is enabled. Else, set"
                " `use-watcher` to false in your local config file."
            )
        insock_path: str | None = local_config.storage_proxy.watcher_insock_path_prefix
        outsock_path: str | None = local_config.storage_proxy.watcher_outsock_path_prefix
        if insock_path is None or outsock_path is None:
            raise InvalidSocketPathError(
                "Socket path must be not null. Please set valid socket path to"
                " `watcher-insock-path-prefix` and `watcher-outsock-path-prefix` in your local"
                " config file."
            )
        watcher_client = WatcherClient(pidx, insock_path, outsock_path)
        await watcher_client.init()
    else:
        watcher_client = None
    try:
        yield watcher_client
    finally:
        if watcher_client is not None:
            await watcher_client.close()


@asynccontextmanager
async def volume_ctx(
    local_config: StorageProxyUnifiedConfig,
    etcd: AsyncEtcd,
    event_dispatcher: EventDispatcher,
    event_producer: EventProducer,
) -> AsyncGenerator[VolumePool]:
    from .volumes.pool import VolumePool

    volume_pool = await VolumePool.create(
        local_config=local_config,
        etcd=etcd,
        event_dispatcher=event_dispatcher,
        event_producer=event_producer,
    )
    try:
        yield volume_pool
    finally:
        await volume_pool.shutdown()


@asynccontextmanager
async def api_ctx(
    local_config: StorageProxyUnifiedConfig,
    etcd: AsyncEtcd,
    root_ctx: RootContext,
) -> AsyncGenerator[tuple[web.Application, web.Application, web.Application]]:
    from .api.client import init_client_app
    from .api.manager import init_internal_app, init_manager_app
    from .plugin import (
        StorageClientWebappPluginContext,
        StorageManagerWebappPluginContext,
        StoragePluginContext,
    )

    @asynccontextmanager
    async def _init_storage_plugin() -> AsyncGenerator[StoragePluginContext]:
        plugin_ctx = StoragePluginContext(etcd, local_config.model_dump())
        await plugin_ctx.init()
        for plugin_name, plugin_instance in plugin_ctx.plugins.items():
            log.info("Loading storage plugin: {0}", plugin_name)
            volume_cls = plugin_instance.get_volume_class()
            root_ctx.backends[plugin_name] = volume_cls
        try:
            yield plugin_ctx
        finally:
            await plugin_ctx.cleanup()

    @asynccontextmanager
    async def _init_storage_webapp_plugin(
        plugin_ctx: BasePluginContext, root_app: web.Application
    ) -> AsyncGenerator[BasePluginContext]:
        pid = os.getpid()
        await plugin_ctx.init()
        for plugin_name, plugin_instance in plugin_ctx.plugins.items():
            if pid == 0:
                log.info("Loading storage webapp plugin: {0}", plugin_name)
            subapp, global_middlewares = await plugin_instance.create_app(root_ctx.cors_options)
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
        await api_init_stack.enter_async_context(_init_storage_plugin())
        client_api_app = await api_init_stack.enter_async_context(client_api_ctx())
        manager_api_app = await api_init_stack.enter_async_context(manager_api_ctx())
        internal_api_app = await api_init_stack.enter_async_context(internal_api_ctx())
        await api_init_stack.enter_async_context(
            _init_storage_webapp_plugin(
                StorageClientWebappPluginContext(etcd, local_config.model_dump()),
                client_api_app,
            )
        )
        await api_init_stack.enter_async_context(
            _init_storage_webapp_plugin(
                StorageManagerWebappPluginContext(etcd, local_config.model_dump()),
                manager_api_app,
            )
        )
        try:
            yield client_api_app, manager_api_app, internal_api_app
        finally:
            # volume instances are lazily initialized upon their first usage by the API layers.
            await root_ctx.shutdown_volumes()
            await root_ctx.shutdown_manager_http_clients()


@asynccontextmanager
async def service_discovery_ctx(
    local_config: StorageProxyUnifiedConfig,
    etcd: AsyncEtcd,
    redis_config: RedisConfig,
) -> AsyncGenerator[None]:
    announce_addr_config = local_config.api.manager.announce_addr
    announce_addr = CommonHostPortPair(
        host=announce_addr_config.host,
        port=announce_addr_config.port,
    )
    announce_internal_addr_config = local_config.api.manager.announce_internal_addr
    announce_internal_addr = CommonHostPortPair(
        host=announce_internal_addr_config.host,
        port=announce_internal_addr_config.port,
    )

    sd_type = local_config.service_discovery.type

    service_discovery: ServiceDiscovery
    match sd_type:
        case ServiceDiscoveryType.ETCD:
            service_discovery = ETCDServiceDiscovery(ETCDServiceDiscoveryArgs(etcd))
        case ServiceDiscoveryType.REDIS:
            valkey_profile_target = redis_config.to_valkey_profile_target()
            live_valkey_target = valkey_profile_target.profile_target(RedisRole.LIVE)
            service_discovery = await RedisServiceDiscovery.create(
                args=RedisServiceDiscoveryArgs(valkey_target=live_valkey_target)
            )

    sd_loop = ServiceDiscoveryLoop(
        sd_type,
        service_discovery,
        ServiceMetadata(
            display_name=f"storage-{local_config.storage_proxy.node_id}",
            service_group="storage-proxy",
            version=VERSION,
            endpoint=ServiceEndpoint(
                address=str(announce_addr),
                port=announce_addr.port,
                protocol="http",
                prometheus_address=str(announce_internal_addr),
            ),
        ),
    )
    if local_config.otel.enabled:
        meta = sd_loop.metadata
        otel_spec = OpenTelemetrySpec(
            service_id=meta.id,
            service_name=meta.service_group,
            service_version=meta.version,
            log_level=local_config.otel.log_level,
            endpoint=local_config.otel.endpoint,
        )
        BraceStyleAdapter.apply_otel(otel_spec)
    try:
        yield
    finally:
        sd_loop.close()


async def _on_prepare(request: web.Request, response: web.StreamResponse) -> None:
    response.headers["Server"] = "BackendAI"


def _init_subapp(
    pkg_name: str,
    root_app: web.Application,
    subapp: web.Application,
    global_middlewares: list[Middleware],
) -> None:
    subapp.on_response_prepare.append(_on_prepare)

    async def _set_root_ctx(subapp: web.Application):
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
    _args: Sequence[Any],
) -> AsyncIterator[None]:
    from .context import DEFAULT_BACKENDS, RootContext
    from .migration import check_latest
    from .storages.storage_pool import StoragePool
    from .volumes.noop import init_noop_volume

    local_config: StorageProxyUnifiedConfig = _args[0]
    loop.set_debug(local_config.debug.asyncio)

    storage_init_stack = AsyncExitStack()
    await storage_init_stack.__aenter__()
    try:
        metric_registry = CommonMetricRegistry()
        monitor = await storage_init_stack.enter_async_context(aiomonitor_ctx(local_config, pidx))
        etcd = await storage_init_stack.enter_async_context(etcd_ctx(local_config))
        redis_config = await storage_init_stack.enter_async_context(redis_ctx(etcd, pidx))
        event_dispatcher, event_producer = await storage_init_stack.enter_async_context(
            event_ctx(local_config, redis_config, pidx, metric_registry)
        )

        # Create StoragePool with both object storage and VFS storage
        volume_pool = await storage_init_stack.enter_async_context(
            volume_ctx(local_config, etcd, event_dispatcher, event_producer)
        )
        storage_pool = StoragePool.from_config(local_config)

        # Clean up temporary storages only on the first process
        if pidx == 0:
            storage_pool.cleanup_temporary_storages()

        bgtask_mgr = await storage_init_stack.enter_async_context(
            bgtask_ctx(local_config, redis_config, event_producer, volume_pool)
        )
        watcher_client = await storage_init_stack.enter_async_context(
            watcher_ctx(local_config, pidx)
        )

        # Create ValkeyArtifactDownloadTrackingClient
        valkey_target = redis_config.to_valkey_target()
        valkey_artifact_client = await ValkeyArtifactDownloadTrackingClient.create(
            valkey_target=valkey_target,
            db_id=REDIS_STATISTICS_DB,
            human_readable_name=f"storage-proxy-artifact-download-tracker-{pidx}",
        )
        storage_init_stack.push_async_callback(valkey_artifact_client.close)

        # Initialize health probe
        health_probe = HealthProbe(options=HealthProbeOptions(check_interval=60))
        await health_probe.register(EtcdHealthChecker(etcd=etcd))
        await health_probe.register(
            ValkeyHealthChecker(
                clients={
                    ComponentId("bgtask"): bgtask_mgr._valkey_client,
                    ComponentId("artifact"): valkey_artifact_client,
                }
            )
        )
        await health_probe.start()
        storage_init_stack.push_async_callback(health_probe.stop)

        # Build reservoir registry configs for ManagerHTTPClientPool
        reservoir_registry_configs: dict[str, ReservoirConfig] = {
            name: r.reservoir
            for name, r in local_config.artifact_registries.items()
            if r.registry_type == ArtifactRegistryType.RESERVOIR and r.reservoir is not None
        }
        for legacy_registry in local_config.registries:
            if isinstance(legacy_registry.config, LegacyReservoirConfig):
                reservoir_registry_configs[legacy_registry.name] = legacy_registry.config

        manager_client_pool = ManagerHTTPClientPool(
            reservoir_registry_configs,
            local_config.reservoir_client,
        )

        root_ctx = RootContext(
            pid=os.getpid(),
            pidx=pidx,
            node_id=local_config.storage_proxy.node_id,
            local_config=local_config,
            etcd=etcd,
            volume_pool=volume_pool,
            storage_pool=storage_pool,
            background_task_manager=bgtask_mgr,
            event_producer=event_producer,
            event_dispatcher=event_dispatcher,
            watcher=watcher_client,
            metric_registry=metric_registry,
            cors_options={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=False, expose_headers="*", allow_headers="*"
                ),
            },
            manager_client_pool=manager_client_pool,
            valkey_artifact_client=valkey_artifact_client,
            health_probe=health_probe,
            backends={**DEFAULT_BACKENDS},
            volumes={
                NOOP_STORAGE_VOLUME_NAME: init_noop_volume(etcd, event_dispatcher, event_producer)
            },
            artifact_verifier_ctx=ArtifactVerifierContext(),
        )
        await root_ctx.init_storage_artifact_verifier_plugin()
        if pidx == 0:
            await check_latest(root_ctx)

        (
            client_api_app,
            manager_api_app,
            internal_api_app,
        ) = await storage_init_stack.enter_async_context(api_ctx(local_config, etcd, root_ctx))
        monitor.console_locals["root_ctx"] = root_ctx
        monitor.console_locals["client_api_app"] = client_api_app
        monitor.console_locals["manager_api_app"] = manager_api_app
        monitor.console_locals["internal_api_app"] = internal_api_app

        await storage_init_stack.enter_async_context(
            service_discovery_ctx(local_config, etcd, redis_config)
        )

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
    from .watcher import main_job

    log_level = LogLevel.DEBUG if debug else log_level
    try:
        local_config = load_local_config(config_path, log_level=log_level)
    except ConfigurationError as e:
        print(
            "ConfigurationError: Could not read or validate the storage-proxy local config:",
            file=sys.stderr,
        )
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort()
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
                match local_config.storage_proxy.event_loop:
                    case EventLoopType.UVLOOP:
                        import uvloop

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

                aiotools.start_server(
                    server_main_logwrapper,
                    num_workers=num_workers,
                    extra_procs=extra_procs,
                    args=(local_config, log_endpoint),
                    runner=runner,
                )
                log.info("exit.")
        finally:
            if local_config.storage_proxy.pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                local_config.storage_proxy.pid_file.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
