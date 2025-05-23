import asyncio
import functools
import grp
import logging
import multiprocessing
import os
import pwd
import ssl
import sys
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from pprint import pformat, pprint
from typing import Any, AsyncIterator, Sequence

import aiomonitor
import aiotools
import click
from aiohttp import web
from setproctitle import setproctitle

from ai.backend.common import redis_helper
from ai.backend.common.config import (
    ConfigurationError,
    override_key,
    redis_config_iv,
)
from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.message_queue.hiredis_queue import HiRedisMQArgs, HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
    ETCDServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscoveryLoop,
    ServiceEndpoint,
    ServiceMetadata,
)
from ai.backend.common.types import (
    AGENTID_STORAGE,
    HostPortPair,
    RedisProfileTarget,
    safe_print_redis_target,
)
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel

from . import __version__ as VERSION
from .config import load_local_config, load_shared_config
from .context import EVENT_DISPATCHER_CONSUMER_GROUP, RootContext
from .watcher import WatcherClient, main_job

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _is_root() -> bool:
    return os.geteuid() == 0


@aiotools.server_context
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Sequence[Any],
) -> AsyncIterator[None]:
    setproctitle(f"backend.ai: storage-proxy worker-{pidx}")
    try:
        asyncio.get_child_watcher()
    except (AttributeError, NotImplementedError):
        pass
    log_endpoint = _args[1]
    logger = Logger(
        _args[0]["logging"],
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


async def check_migration(ctx: RootContext) -> None:
    from .migration import check_latest

    await check_latest(ctx)


@actxmgr
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Sequence[Any],
) -> AsyncIterator[None]:
    local_config = _args[0]
    loop.set_debug(local_config["debug"]["asyncio"])
    m = aiomonitor.Monitor(
        loop,
        termui_port=local_config["storage-proxy"]["aiomonitor-termui-port"] + pidx,
        webui_port=local_config["storage-proxy"]["aiomonitor-webui-port"] + pidx,
        console_enabled=False,
        hook_task_factory=local_config["debug"]["enhanced-aiomonitor-task-info"],
    )
    Profiler(
        pyroscope_args=PyroscopeArgs(
            enabled=local_config["pyroscope"]["enabled"],
            application_name=local_config["pyroscope"]["app-name"],
            server_address=local_config["pyroscope"]["server-addr"],
            sample_rate=local_config["pyroscope"]["sample-rate"],
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
        etcd = load_shared_config(local_config)
        try:
            redis_config = redis_config_iv.check(
                await etcd.get_prefix("config/redis"),
            )
            log.info(
                "PID: {0} - configured redis_config: {1}",
                pidx,
                safe_print_redis_target(redis_config),
            )
        except Exception as e:
            log.exception("Unable to read config from etcd")
            raise e
        redis_profile_target: RedisProfileTarget = RedisProfileTarget.from_dict(redis_config)
        mq = _make_message_queue(
            local_config,
            redis_profile_target,
        )
        event_producer = EventProducer(
            mq,
            source=AGENTID_STORAGE,
            log_events=local_config["debug"]["log-events"],
        )
        log.info(
            "PID: {0} - Event producer created. (redis_config: {1})",
            pidx,
            safe_print_redis_target(redis_config),
        )
        event_dispatcher = EventDispatcher(
            mq,
            log_events=local_config["debug"]["log-events"],
            event_observer=metric_registry.event,
        )
        log.info(
            "PID: {0} - Event dispatcher created. (redis_config: {1})",
            pidx,
            safe_print_redis_target(redis_config),
        )
        if local_config["storage-proxy"]["use-watcher"]:
            if not _is_root():
                raise ValueError(
                    "Storage proxy must be run as root if watcher is enabled. Else, set"
                    " `use-wathcer` to false in your local config file."
                )
            insock_path: str | None = local_config["storage-proxy"]["watcher-insock-path-prefix"]
            outsock_path: str | None = local_config["storage-proxy"]["watcher-outsock-path-prefix"]
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
        ctx = RootContext(
            pid=os.getpid(),
            node_id=local_config["storage-proxy"]["node-id"],
            pidx=pidx,
            local_config=local_config,
            etcd=etcd,
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
            client_api_runner = web.AppRunner(ctx.client_api_app)
            manager_api_runner = web.AppRunner(ctx.manager_api_app)
            internal_api_runner = web.AppRunner(ctx.internal_api_app)
            await client_api_runner.setup()
            await manager_api_runner.setup()
            await internal_api_runner.setup()
            client_service_addr = local_config["api"]["client"]["service-addr"]
            manager_service_addr: HostPortPair = local_config["api"]["manager"]["service-addr"]
            internal_addr = local_config["api"]["manager"]["internal-addr"]
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
                uid = local_config["storage-proxy"]["user"]
                gid = local_config["storage-proxy"]["group"]
                os.setgroups(
                    [g.gr_gid for g in grp.getgrall() if pwd.getpwuid(uid).pw_name in g.gr_mem],
                )
                os.setgid(gid)
                os.setuid(uid)
                log.info("Changed process uid:gid to {}:{}", uid, gid)
            log.info("Started service.")
            announce_addr: HostPortPair = local_config["api"]["manager"]["announce-addr"]
            announce_internal_addr: HostPortPair = local_config["api"]["manager"][
                "announce-internal-addr"
            ]
            etcd_discovery = ETCDServiceDiscovery(ETCDServiceDiscoveryArgs(etcd))
            sd_loop = ServiceDiscoveryLoop(
                etcd_discovery,
                ServiceMetadata(
                    display_name=f"storage-{local_config['storage-proxy']['node-id']}",
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
            try:
                yield
            finally:
                log.info("Shutting down...")
                await manager_api_runner.cleanup()
                await client_api_runner.cleanup()
                await event_producer.close()
                await event_dispatcher.close()
                if watcher_client is not None:
                    await watcher_client.close()
                sd_loop.close()
    finally:
        if aiomon_started:
            m.close()


def _make_message_queue(
    local_config: dict[str, Any],
    redis_profile_target: RedisProfileTarget,
) -> AbstractMessageQueue:
    stream_redis_target = redis_profile_target.profile_target(RedisRole.STREAM)
    stream_redis = redis_helper.get_redis_object(
        stream_redis_target,
        name="event_producer.stream",
        db=REDIS_STREAM_DB,
    )
    node_id = local_config["storage-proxy"]["node-id"]
    if local_config["storage-proxy"].get("use-experimental-redis-event-dispatcher"):
        return HiRedisQueue(
            stream_redis_target,
            HiRedisMQArgs(
                stream_key="events",
                group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
                node_id=node_id,
                db=REDIS_STREAM_DB,
            ),
        )

    return RedisQueue(
        stream_redis,
        RedisMQArgs(
            stream_key="events",
            group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
            node_id=node_id,
        ),
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
    help="Set the logging level to DEBUG",
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
    try:
        local_config = load_local_config(config_path, debug=debug)
    except ConfigurationError as e:
        print(
            "ConfigurationError: Could not read or validate the storage-proxy local config:",
            file=sys.stderr,
        )
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort()
    if debug:
        log_level = LogLevel.DEBUG
    override_key(local_config, ("debug", "enabled"), log_level == LogLevel.DEBUG)
    if log_level != LogLevel.NOTSET:
        override_key(local_config, ("logging", "level"), log_level)
        override_key(local_config, ("logging", "pkg-ns", "ai.backend"), log_level)

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
                msgpack_options={
                    "pack_opts": DEFAULT_PACK_OPTS,
                    "unpack_opts": DEFAULT_UNPACK_OPTS,
                },
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
                insock_path_prefix = local_config["storage-proxy"]["watcher-insock-path-prefix"]
                outsock_path_prefix = local_config["storage-proxy"]["watcher-outsock-path-prefix"]
                num_workers = local_config["storage-proxy"]["num-proc"]

                if local_config["storage-proxy"]["use-watcher"]:
                    if not _is_root():
                        raise ValueError(
                            "Storage proxy must be run as root if watcher is enabled. Else, set"
                            " `use-wathcer` to false in your local config file."
                        )
                    insock_path: str | None = local_config["storage-proxy"][
                        "watcher-insock-path-prefix"
                    ]
                    outsock_path: str | None = local_config["storage-proxy"][
                        "watcher-outsock-path-prefix"
                    ]
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
            if local_config["storage-proxy"]["pid-file"].is_file():
                # check is_file() to prevent deleting /dev/null!
                local_config["storage-proxy"]["pid-file"].unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
