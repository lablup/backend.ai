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
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from pprint import pformat, pprint
from typing import Any, AsyncGenerator, AsyncIterator, Sequence

import aiomonitor
import aiotools
import click
from aiohttp import web
from setproctitle import setproctitle

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.config import (
    ConfigurationError,
)
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.defs import REDIS_BGTASK_DB, REDIS_STREAM_DB, RedisRole
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
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
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel
from ai.backend.logging.otel import OpenTelemetrySpec

from . import __version__ as VERSION
from .config.loaders import load_local_config, make_etcd
from .config.unified import StorageProxyUnifiedConfig

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
    try:
        asyncio.get_child_watcher()
    except (AttributeError, NotImplementedError):
        pass
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
    with logger:
        async with server_main(loop, pidx, _args):
            yield


@actxmgr
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Sequence[Any],
) -> AsyncIterator[None]:
    from .bgtask.registry import BgtaskHandlerRegistryCreator
    from .context import RootContext
    from .migration import check_latest
    from .storages.storage_pool import StoragePool
    from .volumes.pool import VolumePool
    from .watcher import WatcherClient

    local_config: StorageProxyUnifiedConfig = _args[0]
    loop.set_debug(local_config.debug.asyncio)
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
    metric_registry = CommonMetricRegistry()
    try:
        etcd = make_etcd(local_config)
        try:
            raw_redis_config = await etcd.get_prefix("config/redis")
            redis_config = RedisConfig.model_validate(raw_redis_config)
            log.info(
                "PID: {0} - configured redis_config: {1}",
                pidx,
                safe_print_redis_config(redis_config),
            )
        except Exception as e:
            log.exception("Unable to read config from etcd")
            raise e
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
        if local_config.storage_proxy.use_watcher:
            if not _is_root():
                raise ValueError(
                    "Storage proxy must be run as root if watcher is enabled. Else, set"
                    " `use-watcher` to false in your local config file."
                )
            insock_path: str | None = local_config.storage_proxy.watcher_insock_path_prefix
            outsock_path: str | None = local_config.storage_proxy.watcher_outsock_path_prefix
            if insock_path is None or outsock_path is None:
                raise ValueError(
                    "Socket path must be not null. Please set valid socket path to"
                    " `watcher-insock-path-prefix` and `watcher-outsock-path-prefix` in your local"
                    " config file."
                )
            watcher_client = WatcherClient(pidx, insock_path, outsock_path)
            await watcher_client.init()
        else:
            watcher_client = None

        valkey_client = await ValkeyBgtaskClient.create(
            redis_profile_target.profile_target(RedisRole.BGTASK).to_valkey_target(),
            human_readable_name="storage_bgtask",
            db_id=REDIS_BGTASK_DB,
        )
        volume_pool = await VolumePool.create(
            local_config=local_config,
            etcd=etcd,
            event_dispatcher=event_dispatcher,
            event_producer=event_producer,
        )
        bgtask_registry_creator = BgtaskHandlerRegistryCreator(volume_pool, event_producer)
        registry = bgtask_registry_creator.create()
        bgtask_mgr = BackgroundTaskManager(
            event_producer=event_producer,
            task_registry=registry,
            valkey_client=valkey_client,
            server_id=local_config.storage_proxy.node_id,
        )

        # Create StoragePool with both object storage and VFS storage
        storage_pool = StoragePool.from_config(local_config)

        ctx = RootContext(
            pid=os.getpid(),
            node_id=local_config.storage_proxy.node_id,
            pidx=pidx,
            local_config=local_config,
            etcd=etcd,
            volume_pool=volume_pool,
            storage_pool=storage_pool,
            background_task_manager=bgtask_mgr,
            event_producer=event_producer,
            event_dispatcher=event_dispatcher,
            watcher=watcher_client,
            metric_registry=metric_registry,
        )
        async with ctx:
            m.console_locals["ctx"] = ctx
            m.console_locals["client_api_app"] = ctx.client_api_app
            m.console_locals["manager_api_app"] = ctx.manager_api_app

            if pidx == 0:
                await check_latest(ctx)

            client_ssl_ctx = None
            manager_ssl_ctx = None
            if local_config.api.client.ssl_enabled:
                client_ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                client_ssl_ctx.load_cert_chain(
                    str(local_config.api.client.ssl_cert),
                    str(local_config.api.client.ssl_privkey),
                )
            if local_config.api.manager.ssl_enabled:
                manager_ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                manager_ssl_ctx.load_cert_chain(
                    str(local_config.api.manager.ssl_cert),
                    str(local_config.api.manager.ssl_privkey),
                )
            client_api_runner = web.AppRunner(ctx.client_api_app)
            manager_api_runner = web.AppRunner(ctx.manager_api_app)
            internal_api_runner = web.AppRunner(ctx.internal_api_app)
            await client_api_runner.setup()
            await manager_api_runner.setup()
            await internal_api_runner.setup()
            client_service_addr = local_config.api.client.service_addr
            from ai.backend.common.types import HostPortPair as CommonHostPortPair

            manager_service_addr_config = local_config.api.manager.service_addr
            manager_service_addr = CommonHostPortPair(
                host=manager_service_addr_config.host,
                port=manager_service_addr_config.port,
            )
            internal_addr = local_config.api.manager.internal_addr
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
            internal_api_site = web.TCPSite(
                internal_api_runner,
                str(internal_addr.host),
                internal_addr.port,
                backlog=1024,
                reuse_port=True,
            )
            await client_api_site.start()
            await manager_api_site.start()
            await internal_api_site.start()
            if _is_root():
                uid = local_config.storage_proxy.user
                gid = local_config.storage_proxy.group
                if uid is not None and gid is not None:
                    # TODO: Remove this tmp_path handling
                    # after implementing Storage Proxy worker
                    tmp_path = Path("/tmp")
                    for glide_socket in tmp_path.glob("glide-socket-*"):
                        os.chown(glide_socket, uid, gid)
                    os.setgroups(
                        [g.gr_gid for g in grp.getgrall() if pwd.getpwuid(uid).pw_name in g.gr_mem],
                    )
                    os.setgid(gid)
                    os.setuid(uid)
                log.info("Changed process uid:gid to {}:{}", uid, gid)
            log.info("Started service.")
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

            await event_dispatcher.start()
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
                log.info("Shutting down...")
                await manager_api_runner.cleanup()
                await client_api_runner.cleanup()
                await event_producer.close()
                await event_dispatcher.close()
                await valkey_client.close()
                if watcher_client is not None:
                    await watcher_client.close()
                sd_loop.close()
    finally:
        if aiomon_started:
            m.close()


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
                if local_config.storage_proxy.event_loop == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                insock_path_prefix = local_config.storage_proxy.watcher_insock_path_prefix
                outsock_path_prefix = local_config.storage_proxy.watcher_outsock_path_prefix
                num_workers = local_config.storage_proxy.num_proc

                if local_config.storage_proxy.use_watcher:
                    if not _is_root():
                        raise ValueError(
                            "Storage proxy must be run as root if watcher is enabled. Else, set"
                            " `use-watcher` to false in your local config file."
                        )
                    insock_path: str | None = local_config.storage_proxy.watcher_insock_path_prefix
                    outsock_path: str | None = (
                        local_config.storage_proxy.watcher_outsock_path_prefix
                    )
                    if insock_path is None or outsock_path is None:
                        raise ValueError(
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
                )
                log.info("exit.")
        finally:
            if local_config.storage_proxy.pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                local_config.storage_proxy.pid_file.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
