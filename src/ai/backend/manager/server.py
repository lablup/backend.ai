from __future__ import annotations

import asyncio
import functools
import grp
import importlib
import logging
import os
import pwd
import ssl
import sys
import traceback
from contextlib import asynccontextmanager as actxmgr
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Final,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Sequence,
    cast,
)

import aiohttp_cors
import aiomonitor
import aiotools
import click
from aiohttp import web
from redis.asyncio import Redis
from setproctitle import setproctitle

from ai.backend.common import redis_helper
from ai.backend.common.bgtask import BackgroundTaskManager
from ai.backend.common.cli import LazyGroup
from ai.backend.common.events import EventDispatcher, EventProducer
from ai.backend.common.logging import BraceStyleAdapter, Logger
from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookPluginContext
from ai.backend.common.plugin.monitor import INCREMENT
from ai.backend.common.utils import env_info

from . import __version__
from .api import ManagerStatus
from .api.context import RootContext
from .api.exceptions import (
    BackendError,
    GenericBadRequest,
    InternalServerError,
    InvalidAPIParameters,
    MethodNotAllowed,
    URLNotFound,
)
from .api.types import AppCreator, CleanupContext, WebMiddleware, WebRequestHandler
from .config import LocalConfig, SharedConfig
from .config import load as load_config
from .config import volume_config_iv
from .defs import REDIS_IMAGE_DB, REDIS_LIVE_DB, REDIS_STAT_DB, REDIS_STREAM_DB, REDIS_STREAM_LOCK
from .exceptions import InvalidArgument
from .types import DistributedLockFactory

VALID_VERSIONS: Final = frozenset(
    [
        # 'v1.20160915',  # deprecated
        # 'v2.20170315',  # deprecated
        # 'v3.20170615',  # deprecated
        # authentication changed not to use request bodies
        "v4.20181215",
        # added & enabled streaming-execute API
        "v4.20190115",
        # changed resource/image formats
        "v4.20190315",
        # added user mgmt and ID/password authentication
        # added domain/group/scaling-group
        # added domain/group/scaling-group ref. fields to user/keypair/vfolder objects
        "v4.20190615",
        # added mount_map parameter when creating kernel
        # changed GraphQL query structures for multi-container bundled sessions
        "v5.20191215",
        # rewrote vfolder upload/download APIs to migrate to external storage proxies
        "v6.20200815",
        # added standard-compliant /admin/gql endpoint
        # deprecated /admin/graphql endpoint (still present for backward compatibility)
        # added "groups_by_name" GQL query
        # added "filter" and "order" arg to all paginated GQL queries with their own expression mini-langs
        # removed "order_key" and "order_asc" arguments from all paginated GQL queries (never used!)
        "v6.20210815",
        # added session dependencies and state callback URLs configs when creating sessions
        # added session event webhook option to session creation API
        # added architecture option when making image aliases
        "v6.20220315",
        # added payload encryption / decryption on selected transfer
        "v6.20220615",
    ]
)
LATEST_REV_DATES: Final = {
    1: "20160915",
    2: "20170915",
    3: "20181215",
    4: "20190615",
    5: "20191215",
    6: "20220615",
}
LATEST_API_VERSION: Final = "v6.20220615"

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

PUBLIC_INTERFACES: Final = [
    "pidx",
    "background_task_manager",
    "local_config",
    "shared_config",
    "db",
    "registry",
    "redis_live",
    "redis_stat",
    "redis_image",
    "redis_stream",
    "event_dispatcher",
    "event_producer",
    "idle_checkers",
    "storage_manager",
    "stats_monitor",
    "error_monitor",
    "hook_plugin_ctx",
]

public_interface_objs: MutableMapping[str, Any] = {}


async def hello(request: web.Request) -> web.Response:
    """
    Returns the API version number.
    """
    return web.json_response(
        {
            "version": LATEST_API_VERSION,
            "manager": __version__,
        }
    )


async def on_prepare(request: web.Request, response: web.StreamResponse) -> None:
    response.headers["Server"] = "BackendAI"


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
    new_api_version = request.headers.get("X-BackendAI-Version")
    legacy_api_version = request.headers.get("X-Sorna-Version")
    api_version = new_api_version or legacy_api_version
    try:
        if api_version is None:
            path_major_version = int(request.match_info.get("version", 5))
            revision_date = LATEST_REV_DATES[path_major_version]
            request["api_version"] = (path_major_version, revision_date)
        elif api_version in VALID_VERSIONS:
            hdr_major_version, revision_date = api_version.split(".", maxsplit=1)
            request["api_version"] = (int(hdr_major_version[1:]), revision_date)
        else:
            return GenericBadRequest("Unsupported API version.")
    except (ValueError, KeyError):
        return GenericBadRequest("Unsupported API version.")
    resp = await _handler(request)
    return resp


@web.middleware
async def exception_middleware(
    request: web.Request, handler: WebRequestHandler
) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    error_monitor = root_ctx.error_monitor
    stats_monitor = root_ctx.stats_monitor
    try:
        await stats_monitor.report_metric(INCREMENT, "ai.backend.manager.api.requests")
        resp = await handler(request)
    except InvalidArgument as ex:
        if len(ex.args) > 1:
            raise InvalidAPIParameters(f"{ex.args[0]}: {', '.join(map(str, ex.args[1:]))}")
        elif len(ex.args) == 1:
            raise InvalidAPIParameters(ex.args[0])
        else:
            raise InvalidAPIParameters()
    except BackendError as ex:
        if ex.status_code == 500:
            log.warning("Internal server error raised inside handlers")
        await error_monitor.capture_exception()
        await stats_monitor.report_metric(INCREMENT, "ai.backend.manager.api.failures")
        await stats_monitor.report_metric(
            INCREMENT, f"ai.backend.manager.api.status.{ex.status_code}"
        )
        raise
    except web.HTTPException as ex:
        await stats_monitor.report_metric(INCREMENT, "ai.backend.manager.api.failures")
        await stats_monitor.report_metric(
            INCREMENT, f"ai.backend.manager.api.status.{ex.status_code}"
        )
        if ex.status_code == 404:
            raise URLNotFound(extra_data=request.path)
        if ex.status_code == 405:
            concrete_ex = cast(web.HTTPMethodNotAllowed, ex)
            raise MethodNotAllowed(concrete_ex.method, concrete_ex.allowed_methods)
        log.warning("Bad request: {0!r}", ex)
        raise GenericBadRequest
    except asyncio.CancelledError as e:
        # The server is closing or the client has disconnected in the middle of
        # request.  Atomic requests are still executed to their ends.
        log.debug("Request cancelled ({0} {1})", request.method, request.rel_url)
        raise e
    except Exception as e:
        await error_monitor.capture_exception()
        log.exception("Uncaught exception in HTTP request handlers {0!r}", e)
        if root_ctx.local_config["debug"]["enabled"]:
            raise InternalServerError(traceback.format_exc())
        else:
            raise InternalServerError()
    else:
        await stats_monitor.report_metric(INCREMENT, f"ai.backend.manager.api.status.{resp.status}")
        return resp


@actxmgr
async def shared_config_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    # populate public interfaces
    root_ctx.shared_config = SharedConfig(
        root_ctx.local_config["etcd"]["addr"],
        root_ctx.local_config["etcd"]["user"],
        root_ctx.local_config["etcd"]["password"],
        root_ctx.local_config["etcd"]["namespace"],
    )
    await root_ctx.shared_config.reload()
    yield
    await root_ctx.shared_config.close()


@actxmgr
async def webapp_plugin_ctx(root_app: web.Application) -> AsyncIterator[None]:
    from .plugin.webapp import WebappPluginContext

    root_ctx: RootContext = root_app["_root.context"]
    plugin_ctx = WebappPluginContext(root_ctx.shared_config.etcd, root_ctx.local_config)
    await plugin_ctx.init(
        allowlist=root_ctx.local_config["manager"]["allowed-plugins"],
        blocklist=root_ctx.local_config["manager"]["disabled-plugins"],
    )
    root_ctx.webapp_plugin_ctx = plugin_ctx
    for plugin_name, plugin_instance in plugin_ctx.plugins.items():
        if root_ctx.pidx == 0:
            log.info("Loading webapp plugin: {0}", plugin_name)
        subapp, global_middlewares = await plugin_instance.create_app(root_ctx.cors_options)
        _init_subapp(plugin_name, root_app, subapp, global_middlewares)
    yield
    await plugin_ctx.cleanup()


@actxmgr
async def manager_status_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    if root_ctx.pidx == 0:
        mgr_status = await root_ctx.shared_config.get_manager_status()
        if mgr_status is None or mgr_status not in (ManagerStatus.RUNNING, ManagerStatus.FROZEN):
            # legacy transition: we now have only RUNNING or FROZEN for HA setup.
            await root_ctx.shared_config.update_manager_status(ManagerStatus.RUNNING)
            mgr_status = ManagerStatus.RUNNING
        log.info("Manager status: {}", mgr_status)
        tz = root_ctx.shared_config["system"]["timezone"]
        log.info("Configured timezone: {}", tz.tzname(datetime.now()))
    yield


@actxmgr
async def redis_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.redis_live = redis_helper.get_redis_object(
        root_ctx.shared_config.data["redis"],
        db=REDIS_LIVE_DB,
    )
    root_ctx.redis_stat = redis_helper.get_redis_object(
        root_ctx.shared_config.data["redis"],
        db=REDIS_STAT_DB,
    )
    root_ctx.redis_image = redis_helper.get_redis_object(
        root_ctx.shared_config.data["redis"],
        db=REDIS_IMAGE_DB,
    )
    root_ctx.redis_stream = redis_helper.get_redis_object(
        root_ctx.shared_config.data["redis"],
        db=REDIS_STREAM_DB,
    )
    root_ctx.redis_lock = redis_helper.get_redis_object(
        root_ctx.shared_config.data["redis"],
        db=REDIS_STREAM_LOCK,
    )
    for redis_info in (
        root_ctx.redis_live,
        root_ctx.redis_stat,
        root_ctx.redis_image,
        root_ctx.redis_stream,
        root_ctx.redis_lock,
    ):
        assert isinstance(redis_info.client, Redis)
        await redis_helper.ping_redis_connection(redis_info.client)
    yield
    await root_ctx.redis_stream.close()
    await root_ctx.redis_image.close()
    await root_ctx.redis_stat.close()
    await root_ctx.redis_live.close()
    await root_ctx.redis_lock.close()


@actxmgr
async def database_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .models.utils import connect_database

    async with connect_database(root_ctx.local_config) as db:
        root_ctx.db = db
        yield


@actxmgr
async def distributed_lock_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.distributed_lock_factory = init_lock_factory(root_ctx)
    yield


@actxmgr
async def event_dispatcher_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.event_producer = await EventProducer.new(
        root_ctx.shared_config.data["redis"],
        db=REDIS_STREAM_DB,
    )
    root_ctx.event_dispatcher = await EventDispatcher.new(
        root_ctx.shared_config.data["redis"],
        db=REDIS_STREAM_DB,
        log_events=root_ctx.local_config["debug"]["log-events"],
        node_id=root_ctx.local_config["manager"]["id"],
    )
    yield
    await root_ctx.event_producer.close()
    await asyncio.sleep(0.2)
    await root_ctx.event_dispatcher.close()


@actxmgr
async def idle_checker_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .idle import init_idle_checkers

    root_ctx.idle_checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await root_ctx.idle_checker_host.start()
    yield
    await root_ctx.idle_checker_host.shutdown()


@actxmgr
async def storage_manager_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .models.storage import StorageSessionManager

    raw_vol_config = await root_ctx.shared_config.etcd.get_prefix("volumes")
    config = volume_config_iv.check(raw_vol_config)
    root_ctx.storage_manager = StorageSessionManager(config)
    yield
    await root_ctx.storage_manager.aclose()


@actxmgr
async def hook_plugin_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    ctx = HookPluginContext(root_ctx.shared_config.etcd, root_ctx.local_config)
    root_ctx.hook_plugin_ctx = ctx
    await ctx.init(
        allowlist=root_ctx.local_config["manager"]["allowed-plugins"],
        blocklist=root_ctx.local_config["manager"]["disabled-plugins"],
    )
    hook_result = await ctx.dispatch(
        "ACTIVATE_MANAGER",
        (),
        return_when=ALL_COMPLETED,
    )
    if hook_result.status != PASSED:
        raise RuntimeError("Could not activate the manager instance.")
    yield
    await ctx.cleanup()


@actxmgr
async def agent_registry_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .registry import AgentRegistry

    root_ctx.registry = AgentRegistry(
        root_ctx.shared_config,
        root_ctx.db,
        root_ctx.redis_stat,
        root_ctx.redis_live,
        root_ctx.redis_image,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.storage_manager,
        root_ctx.hook_plugin_ctx,
    )
    await root_ctx.registry.init()
    yield
    await root_ctx.registry.shutdown()


@actxmgr
async def sched_dispatcher_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .scheduler.dispatcher import SchedulerDispatcher

    sched_dispatcher = await SchedulerDispatcher.new(
        root_ctx.local_config,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
        root_ctx.registry,
    )
    yield
    await sched_dispatcher.close()


@actxmgr
async def monitoring_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .plugin.monitor import ManagerErrorPluginContext, ManagerStatsPluginContext

    ectx = ManagerErrorPluginContext(root_ctx.shared_config.etcd, root_ctx.local_config)
    sctx = ManagerStatsPluginContext(root_ctx.shared_config.etcd, root_ctx.local_config)
    init_success = False
    try:
        await ectx.init(
            context={"_root.context": root_ctx},
            allowlist=root_ctx.local_config["manager"]["allowed-plugins"],
        )
        await sctx.init(allowlist=root_ctx.local_config["manager"]["allowed-plugins"])
    except Exception:
        log.error("Failed to initialize monitoring plugins")
    else:
        init_success = True
        root_ctx.error_monitor = ectx
        root_ctx.stats_monitor = sctx
    yield
    if init_success:
        await sctx.cleanup()
        await ectx.cleanup()


class background_task_ctx:
    def __init__(self, root_ctx: RootContext) -> None:
        self.root_ctx = root_ctx

    async def __aenter__(self) -> None:
        self.root_ctx.background_task_manager = BackgroundTaskManager(self.root_ctx.event_producer)

    async def __aexit__(self, *exc_info) -> None:
        pass

    async def shutdown(self) -> None:
        if hasattr(self.root_ctx, "background_task_manager"):
            await self.root_ctx.background_task_manager.shutdown()


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
            if (error_monitor := getattr(root_ctx, "error_monitor", None)) is not None:
                loop.create_task(error_monitor.capture_exception())
        else:
            exc_info = (type(exception), exception, exception.__traceback__)
            log.error("Error inside event loop: {0}", msg, exc_info=exc_info)
            if (error_monitor := getattr(root_ctx, "error_monitor", None)) is not None:
                loop.create_task(error_monitor.capture_exception(exc_instance=exception))


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
    prefix = subapp.get("prefix", pkg_name.split(".")[-1].replace("_", "-"))
    root_app.add_subapp("/" + prefix, subapp)
    root_app.middlewares.extend(global_middlewares)


def init_subapp(pkg_name: str, root_app: web.Application, create_subapp: AppCreator) -> None:
    root_ctx: RootContext = root_app["_root.context"]
    subapp, global_middlewares = create_subapp(root_ctx.cors_options)
    _init_subapp(pkg_name, root_app, subapp, global_middlewares)


def init_lock_factory(root_ctx: RootContext) -> DistributedLockFactory:
    ipc_base_path = root_ctx.local_config["manager"]["ipc-base-path"]
    manager_id = root_ctx.local_config["manager"]["id"]
    lock_backend = root_ctx.local_config["manager"]["distributed-lock"]
    log.debug("using {} as the distributed lock backend", lock_backend)
    match lock_backend:
        case "filelock":
            from ai.backend.common.lock import FileLock

            return lambda lock_id, lifetime_hint: FileLock(
                ipc_base_path / f"{manager_id}.{lock_id}.lock",
                timeout=0,
            )
        case "pg_advisory":
            from .pglock import PgAdvisoryLock

            return lambda lock_id, lifetime_hint: PgAdvisoryLock(root_ctx.db, lock_id)
        case "redlock":
            from ai.backend.common.lock import RedisLock

            return lambda lock_id, lifetime_hint: RedisLock(
                str(lock_id),
                root_ctx.redis_lock,
                lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
            )
        case "etcd":
            from ai.backend.common.lock import EtcdLock

            return lambda lock_id, lifetime_hint: EtcdLock(
                str(lock_id),
                root_ctx.shared_config.etcd,
                lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
            )
        case other:
            raise ValueError(f"Invalid lock backend: {other}")


def build_root_app(
    pidx: int,
    local_config: LocalConfig,
    *,
    cleanup_contexts: Sequence[CleanupContext] = None,
    subapp_pkgs: Sequence[str] = None,
    scheduler_opts: Mapping[str, Any] = None,
) -> web.Application:
    public_interface_objs.clear()
    app = web.Application(
        middlewares=[
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
    default_scheduler_opts = {
        "limit": 2048,
        "close_timeout": 30,
        "exception_handler": global_exception_handler,
    }
    app["scheduler_opts"] = {
        **default_scheduler_opts,
        **(scheduler_opts if scheduler_opts is not None else {}),
    }
    app.on_response_prepare.append(on_prepare)

    if cleanup_contexts is None:
        cleanup_contexts = [
            manager_status_ctx,
            redis_ctx,
            database_ctx,
            distributed_lock_ctx,
            event_dispatcher_ctx,
            idle_checker_ctx,
            storage_manager_ctx,
            hook_plugin_ctx,
            monitoring_ctx,
            agent_registry_ctx,
            sched_dispatcher_ctx,
            background_task_ctx,
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
    if subapp_pkgs is None:
        subapp_pkgs = []
    for pkg_name in subapp_pkgs:
        if pidx == 0:
            log.info("Loading module: {0}", pkg_name[1:])
        subapp_mod = importlib.import_module(pkg_name, "ai.backend.manager.api")
        init_subapp(pkg_name, app, getattr(subapp_mod, "create_app"))
    return app


@actxmgr
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: List[Any],
) -> AsyncIterator[None]:
    subapp_pkgs = [
        ".acl",
        ".etcd",
        ".events",
        ".auth",
        ".ratelimit",
        ".vfolder",
        ".admin",
        ".session",
        ".stream",
        ".manager",
        ".resource",
        ".scaling_group",
        ".cluster_template",
        ".session_template",
        ".image",
        ".userconfig",
        ".domainconfig",
        ".groupconfig",
        ".logs",
    ]
    root_app = build_root_app(pidx, _args[0], subapp_pkgs=subapp_pkgs)
    root_ctx: RootContext = root_app["_root.context"]

    # Start aiomonitor.
    # Port is set by config (default=50100 + pidx).
    loop.set_debug(root_ctx.local_config["debug"]["asyncio"])
    m = aiomonitor.Monitor(
        loop,
        port=root_ctx.local_config["manager"]["aiomonitor-port"] + pidx,
        console_enabled=False,
        hook_task_factory=root_ctx.local_config["debug"]["enhanced-aiomonitor-task-info"],
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
        async with (
            shared_config_ctx(root_ctx),
            webapp_plugin_ctx(root_app),
        ):
            ssl_ctx = None
            if root_ctx.local_config["manager"]["ssl-enabled"]:
                ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_ctx.load_cert_chain(
                    str(root_ctx.local_config["manager"]["ssl-cert"]),
                    str(root_ctx.local_config["manager"]["ssl-privkey"]),
                )

            runner = web.AppRunner(root_app, keepalive_timeout=30.0)
            await runner.setup()
            service_addr = root_ctx.local_config["manager"]["service-addr"]
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
                uid = root_ctx.local_config["manager"]["user"]
                gid = root_ctx.local_config["manager"]["group"]
                os.setgroups(
                    [g.gr_gid for g in grp.getgrall() if pwd.getpwuid(uid).pw_name in g.gr_mem]
                )
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
    _args: List[Any],
) -> AsyncIterator[None]:
    setproctitle(f"backend.ai: manager worker-{pidx}")
    log_endpoint = _args[1]
    logger = Logger(_args[0]["logging"], is_master=False, log_endpoint=log_endpoint)
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
    help="Enable the debug mode and override the global log level to DEBUG.",
)
@click.pass_context
def main(ctx: click.Context, config_path: Path, debug: bool) -> None:
    """
    Start the manager service as a foreground process.
    """

    cfg = load_config(config_path, debug)

    if ctx.invoked_subcommand is None:
        cfg["manager"]["pid-file"].write_text(str(os.getpid()))
        ipc_base_path = cfg["manager"]["ipc-base-path"]
        log_sockpath = ipc_base_path / f"manager-logger-{os.getpid()}.sock"
        log_endpoint = f"ipc://{log_sockpath}"
        try:
            logger = Logger(cfg["logging"], is_master=True, log_endpoint=log_endpoint)
            with logger:
                ns = cfg["etcd"]["namespace"]
                setproctitle(f"backend.ai: manager {ns}")
                log.info("Backend.AI Manager {0}", __version__)
                log.info("runtime: {0}", env_info())
                log_config = logging.getLogger("ai.backend.manager.config")
                log_config.debug("debug mode enabled.")
                if cfg["manager"]["event-loop"] == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                try:
                    aiotools.start_server(
                        server_main_logwrapper,
                        num_workers=cfg["manager"]["num-proc"],
                        args=(cfg, log_endpoint),
                        wait_timeout=5.0,
                    )
                finally:
                    log.info("terminated.")
        finally:
            if cfg["manager"]["pid-file"].is_file():
                # check is_file() to prevent deleting /dev/null!
                cfg["manager"]["pid-file"].unlink()
    else:
        # Click is going to invoke a subcommand.
        pass


@main.group(cls=LazyGroup, import_name="ai.backend.manager.api.auth:cli")
def auth() -> None:
    pass


if __name__ == "__main__":
    sys.exit(main())
