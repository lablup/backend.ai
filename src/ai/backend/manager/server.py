from __future__ import annotations

import asyncio
import functools
import grp
import importlib
import importlib.resources
import logging
import os
import pwd
import signal
import ssl
import sys
import traceback
from collections.abc import (
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
)
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
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
from aiohttp.typedefs import Handler, Middleware
from setproctitle import setproctitle

from ai.backend.common import redis_helper
from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.cli import LazyGroup
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.config import find_config_file
from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.common.defs import (
    REDIS_BGTASK_DB,
    REDIS_CONTAINER_LOG,
    REDIS_IMAGE_DB,
    REDIS_LIVE_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
    REDIS_STREAM_LOCK,
    RedisRole,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.events.event_types.artifact_registry.anycast import (
    DoScanReservoirRegistryEvent,
)
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.common.json import dump_json_str
from ai.backend.common.leader.tasks.event_task import EventTaskSpec
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.metrics.http import (
    build_api_metric_middleware,
    build_prometheus_metrics_handler,
)
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.middlewares.request_id import request_id_middleware
from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookPluginContext
from ai.backend.common.plugin.monitor import INCREMENT
from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
    ETCDServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.redis_discovery.service_discovery import (
    RedisServiceDiscovery,
    RedisServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscoveryLoop,
    ServiceEndpoint,
    ServiceMetadata,
)
from ai.backend.common.types import (
    AGENTID_MANAGER,
    AgentSelectionStrategy,
    ServiceDiscoveryType,
)
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel
from ai.backend.logging.otel import OpenTelemetrySpec
from ai.backend.manager.config.bootstrap import BootstrapConfig
from ai.backend.manager.config.loader.config_overrider import ConfigOverrider
from ai.backend.manager.config.loader.etcd_loader import (
    EtcdCommonConfigLoader,
    EtcdManagerConfigLoader,
)
from ai.backend.manager.config.loader.legacy_etcd_loader import (
    LegacyEtcdLoader,
    LegacyEtcdVolumesLoader,
)
from ai.backend.manager.config.loader.loader_chain import LoaderChain
from ai.backend.manager.config.loader.toml_loader import TomlConfigLoader
from ai.backend.manager.config.loader.types import AbstractConfigLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.watchers.etcd import EtcdConfigWatcher
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)
from ai.backend.manager.sokovan.deployment.route.route_controller import (
    RouteController,
    RouteControllerArgs,
)

from . import __version__
from .api.context import RootContext
from .types import DistributedLockFactory, SMTPTriggerPolicy

if TYPE_CHECKING:
    from ai.backend.manager.reporters.base import AbstractReporter

    from .api.types import (
        AppCreator,
        CleanupContext,
        WebRequestHandler,
    )

VALID_VERSIONS: Final = frozenset([
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
    # added config/resource-slots/details, model mgmt & serving APIs
    "v6.20230315",
    # added quota scopes (per-user/per-project quota configs)
    # added user & project resource policies
    # deprecated per-vfolder quota configs (BREAKING)
    "v7.20230615",
    # added /vfolders API set to replace name-based refs to ID-based refs to work with vfolders
    # set pending deprecation for the legacy /folders API set
    # added vfolder trash bin APIs
    # changed the image registry management API to allow per-project registry configs (BREAKING)
    "v8.20240315",
    # added session priority and Relay-compliant ComputeSessioNode, KernelNode queries
    # added dependents/dependees/graph query fields to ComputeSessioNode
    "v8.20240915",
    # added explicit attach_network option to session creation config
    "v9.20250722",
    # added model_ids, model_id_map options to session creation config
    # <future>
    # TODO: replaced keypair-based resource policies to user-based resource policies
    # TODO: began SSO support using per-external-service keypairs (e.g., for FastTrack)
    # TODO: added an initial version of RBAC for projects and vfolders
])
LATEST_REV_DATES: Final = {
    1: "20160915",
    2: "20170915",
    3: "20181215",
    4: "20190615",
    5: "20191215",
    6: "20230315",
    7: "20230615",
    8: "20240915",
    9: "20250722",
}
LATEST_API_VERSION: Final = "v9.20250722"

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

PUBLIC_INTERFACES: Final = [
    "pidx",
    "background_task_manager",
    "db",
    "registry",
    "redis_live",
    "valkey_stat_client",
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

global_subapp_pkgs: Final[list[str]] = [
    ".acl",
    ".container_registry",
    ".artifact",
    ".artifact_registry",
    ".etcd",
    ".events",
    ".auth",
    ".ratelimit",
    ".vfolder",
    ".admin",
    ".spec",
    ".service",
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
    ".group",
    ".groupconfig",
    ".logs",
    ".object_storage",
]

global_subapp_pkgs_for_public_metrics_app: Final[tuple[str, ...]] = (".health",)

EVENT_DISPATCHER_CONSUMER_GROUP: Final = "manager"


async def hello(request: web.Request) -> web.Response:
    """
    Returns the API version number.
    """
    return web.json_response({
        "version": LATEST_API_VERSION,
        "manager": __version__,
    })


async def on_prepare(request: web.Request, response: web.StreamResponse) -> None:
    response.headers["Server"] = "BackendAI"


@web.middleware
async def api_middleware(request: web.Request, handler: WebRequestHandler) -> web.StreamResponse:
    from .errors.common import GenericBadRequest, InternalServerError

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


def _debug_error_response(
    e: Exception,
) -> web.StreamResponse:
    error_type = ""
    error_title = ""
    error_message = "Internal server error"
    status_code = 500
    error_code = ErrorCode.default()
    if isinstance(e, BackendAIError):
        error_type = e.error_type
        error_title = e.error_title
        if e.extra_msg:
            error_message = e.extra_msg
        status_code = e.status_code
        error_code = e.error_code()

    return web.json_response(
        {
            "type": error_type,
            "title": error_title,
            "error_code": str(error_code),
            "msg": error_message,
            "traceback": traceback.format_exc(),
        },
        status=status_code,
        dumps=dump_json_str,
    )


@web.middleware
async def exception_middleware(
    request: web.Request, handler: WebRequestHandler
) -> web.StreamResponse:
    from .errors.api import InvalidAPIParameters
    from .errors.common import (
        GenericBadRequest,
        InternalServerError,
        MethodNotAllowed,
        URLNotFound,
    )
    from .exceptions import InvalidArgument

    root_ctx: RootContext = request.app["_root.context"]
    error_monitor = root_ctx.error_monitor
    stats_monitor = root_ctx.stats_monitor
    method = request.method
    endpoint = getattr(request.match_info.route.resource, "canonical", request.path)
    try:
        await stats_monitor.report_metric(INCREMENT, "ai.backend.manager.api.requests")
        resp = await handler(request)
    # NOTE: pydantic.ValidationError is handled in utils.pydantic_params_api_handler()
    except InvalidArgument as ex:
        if len(ex.args) > 1:
            raise InvalidAPIParameters(f"{ex.args[0]}: {', '.join(map(str, ex.args[1:]))}")
        elif len(ex.args) == 1:
            raise InvalidAPIParameters(ex.args[0])
        else:
            raise InvalidAPIParameters()
    except BackendAIError as ex:
        if ex.status_code // 100 == 4:
            log.warning(
                "client error raised inside handlers: ({} {}): {}", method, endpoint, repr(ex)
            )
        elif ex.status_code // 100 == 5:
            log.exception(
                "Internal server error raised inside handlers: ({} {}): {}",
                method,
                endpoint,
                repr(ex),
            )
        await error_monitor.capture_exception()
        await stats_monitor.report_metric(INCREMENT, "ai.backend.manager.api.failures")
        await stats_monitor.report_metric(
            INCREMENT, f"ai.backend.manager.api.status.{ex.status_code}"
        )
        if root_ctx.config_provider.config.debug.enabled:
            return _debug_error_response(ex)
        raise
    except web.HTTPException as ex:
        await stats_monitor.report_metric(INCREMENT, "ai.backend.manager.api.failures")
        await stats_monitor.report_metric(
            INCREMENT, f"ai.backend.manager.api.status.{ex.status_code}"
        )
        if ex.status_code // 100 == 4:
            log.warning("client error raised inside handlers: ({} {}): {}", method, endpoint, ex)
        elif ex.status_code // 100 == 5:
            log.exception(
                "Internal server error raised inside handlers: ({} {}): {}", method, endpoint, ex
            )
        if ex.status_code == 404:
            raise URLNotFound(extra_data=request.path)
        if ex.status_code == 405:
            concrete_ex = cast(web.HTTPMethodNotAllowed, ex)
            raise MethodNotAllowed(
                method=concrete_ex.method, allowed_methods=concrete_ex.allowed_methods
            )
        raise GenericBadRequest
    except asyncio.CancelledError as e:
        # The server is closing or the client has disconnected in the middle of
        # request.  Atomic requests are still executed to their ends.
        log.debug("Request cancelled ({0} {1})", request.method, request.rel_url)
        raise e
    except Exception as e:
        await error_monitor.capture_exception()
        log.exception(
            "Uncaught exception in HTTP request handlers ({} {}): {}", method, endpoint, e
        )
        if root_ctx.config_provider.config.debug.enabled:
            return _debug_error_response(e)
        else:
            raise InternalServerError()
    else:
        await stats_monitor.report_metric(INCREMENT, f"ai.backend.manager.api.status.{resp.status}")
        return resp


@actxmgr
async def etcd_ctx(root_ctx: RootContext, etcd_config: EtcdConfigData) -> AsyncIterator[None]:
    root_ctx.etcd = AsyncEtcd.initialize(etcd_config)
    yield
    await root_ctx.etcd.close()


@actxmgr
async def config_provider_ctx(
    root_ctx: RootContext,
    log_level: LogLevel,
    config_path: Optional[Path] = None,
    extra_config: Optional[Mapping[str, Any]] = None,
) -> AsyncIterator[ManagerConfigProvider]:
    loaders: list[AbstractConfigLoader] = []

    if config_path:
        toml_config_loader = TomlConfigLoader(config_path, "manager")
        loaders.append(toml_config_loader)
    else:
        log.warning("No config file path specified. Skipped loading toml config file...")

    legacy_etcd_loader = LegacyEtcdLoader(root_ctx.etcd)
    loaders.append(legacy_etcd_loader)
    loaders.append(LegacyEtcdVolumesLoader(root_ctx.etcd))
    loaders.append(EtcdCommonConfigLoader(root_ctx.etcd))
    loaders.append(EtcdManagerConfigLoader(root_ctx.etcd))

    overrides: list[tuple[tuple[str, ...], Any]] = [
        (("debug", "enabled"), log_level == LogLevel.DEBUG),
    ]
    if log_level != LogLevel.NOTSET:
        overrides += [
            (("logging", "level"), log_level),
            (("logging", "pkg-ns", "ai.backend"), log_level),
        ]

    loaders.append(ConfigOverrider(overrides))

    unified_config_loader = LoaderChain(loaders, base_config=extra_config)
    etcd_watcher = EtcdConfigWatcher(root_ctx.etcd)

    config_provider: Optional[ManagerConfigProvider] = None
    try:
        config_provider = await ManagerConfigProvider.create(
            unified_config_loader,
            etcd_watcher,
            legacy_etcd_loader,
        )
        root_ctx.config_provider = config_provider

        if config_provider.config.debug.enabled and root_ctx.pidx == 0:
            print("== Manager configuration ==", file=sys.stderr)
            print(pformat(config_provider.config), file=sys.stderr)
        yield root_ctx.config_provider
    finally:
        if config_provider:
            await config_provider.terminate()


@actxmgr
async def webapp_plugin_ctx(root_app: web.Application) -> AsyncIterator[None]:
    from .plugin.webapp import WebappPluginContext

    root_ctx: RootContext = root_app["_root.context"]
    plugin_ctx = WebappPluginContext(
        root_ctx.etcd,
        root_ctx.config_provider.config.model_dump(by_alias=True),
    )
    await plugin_ctx.init(
        context=root_ctx,
        allowlist=root_ctx.config_provider.config.manager.allowed_plugins,
        blocklist=root_ctx.config_provider.config.manager.disabled_plugins,
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
    from .api import ManagerStatus

    if root_ctx.pidx == 0:
        mgr_status = await root_ctx.config_provider.legacy_etcd_config_loader.get_manager_status()
        if mgr_status is None or mgr_status not in (ManagerStatus.RUNNING, ManagerStatus.FROZEN):
            # legacy transition: we now have only RUNNING or FROZEN for HA setup.
            await root_ctx.config_provider.legacy_etcd_config_loader.update_manager_status(
                ManagerStatus.RUNNING
            )
            mgr_status = ManagerStatus.RUNNING
        log.info("Manager status: {}", mgr_status)
        tz = root_ctx.config_provider.config.system.timezone
        log.info("Configured timezone: {}", tz.tzname(datetime.now()))
    yield


@actxmgr
async def redis_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    valkey_profile_target = root_ctx.config_provider.config.redis.to_valkey_profile_target()
    root_ctx.valkey_profile_target = valkey_profile_target

    root_ctx.valkey_container_log = await ValkeyContainerLogClient.create(
        valkey_profile_target.profile_target(RedisRole.CONTAINER_LOG),
        db_id=REDIS_CONTAINER_LOG,
        human_readable_name="container_log",  # saving container_log queue
    )
    root_ctx.valkey_live = await ValkeyLiveClient.create(
        valkey_profile_target.profile_target(RedisRole.LIVE),
        db_id=REDIS_LIVE_DB,
        human_readable_name="live",  # tracking live status of various entities
    )
    root_ctx.valkey_stat = await ValkeyStatClient.create(
        valkey_profile_target.profile_target(RedisRole.STATISTICS),
        db_id=REDIS_STATISTICS_DB,
        human_readable_name="stat",  # temporary storage for stat snapshots
    )
    root_ctx.valkey_image = await ValkeyImageClient.create(
        valkey_profile_target.profile_target(RedisRole.IMAGE),
        db_id=REDIS_IMAGE_DB,
        human_readable_name="image",  # per-agent image availability
    )
    root_ctx.valkey_stream = await ValkeyStreamClient.create(
        valkey_profile_target.profile_target(RedisRole.STREAM),
        human_readable_name="stream",
        db_id=REDIS_STREAM_DB,
    )
    root_ctx.valkey_schedule = await ValkeyScheduleClient.create(
        valkey_profile_target.profile_target(RedisRole.STREAM),
        db_id=REDIS_LIVE_DB,
        human_readable_name="schedule",  # scheduling marks and coordination
    )
    root_ctx.valkey_bgtask = await ValkeyBgtaskClient.create(
        valkey_profile_target.profile_target(RedisRole.BGTASK),
        human_readable_name="bgtask",
        db_id=REDIS_BGTASK_DB,
    )
    # Ping ValkeyLiveClient directly
    await root_ctx.valkey_live.get_server_time()
    # ValkeyImageClient has its own connection handling
    # No need to ping it separately as it's already connected
    yield
    await root_ctx.valkey_container_log.close()
    await root_ctx.valkey_image.close()
    await root_ctx.valkey_stat.close()
    await root_ctx.valkey_live.close()
    await root_ctx.valkey_stream.close()
    await root_ctx.valkey_schedule.close()
    await root_ctx.valkey_bgtask.close()


@actxmgr
async def database_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .models.utils import connect_database

    async with connect_database(root_ctx.config_provider.config.db) as db:
        root_ctx.db = db
        yield


def _make_registered_reporters(
    root_ctx: RootContext,
) -> dict[str, AbstractReporter]:
    from .reporters.smtp import SMTPReporter, SMTPSenderArgs

    reporters: dict[str, AbstractReporter] = {}
    smtp_configs = root_ctx.config_provider.config.reporter.smtp
    for smtp_conf in smtp_configs:
        smtp_args = SMTPSenderArgs(
            host=smtp_conf.host,
            port=smtp_conf.port,
            username=smtp_conf.username,
            password=smtp_conf.password,
            sender=smtp_conf.sender,
            recipients=smtp_conf.recipients,
            use_tls=smtp_conf.use_tls,
            max_workers=smtp_conf.max_workers,
            template=smtp_conf.template,
        )
        trigger_policy = SMTPTriggerPolicy[smtp_conf.trigger_policy]
        reporters[smtp_conf.name] = SMTPReporter(smtp_args, trigger_policy)

    return reporters


def _make_action_reporters(
    root_ctx: RootContext,
    reporters: dict[str, AbstractReporter],
) -> dict[str, list[AbstractReporter]]:
    action_monitors: dict[str, list[AbstractReporter]] = {}
    action_monitor_configs = root_ctx.config_provider.config.reporter.action_monitors
    for action_monitor_conf in action_monitor_configs:
        reporter_name: str = action_monitor_conf.reporter
        try:
            reporter = reporters[reporter_name]
        except KeyError:
            log.warning(f'Invalid Reporter: "{reporter_name}"')
            continue

        for action_type in action_monitor_conf.subscribed_actions:
            action_monitors.setdefault(action_type, []).append(reporter)

    return action_monitors


@actxmgr
async def processors_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .actions.monitors.audit_log import AuditLogMonitor
    from .actions.monitors.prometheus import PrometheusMonitor
    from .actions.monitors.reporter import ReporterMonitor
    from .reporters.hub import ReporterHub, ReporterHubArgs
    from .services.processors import ProcessorArgs, Processors, ServiceArgs

    registered_reporters = _make_registered_reporters(root_ctx)
    action_reporters = _make_action_reporters(root_ctx, registered_reporters)
    reporter_hub = ReporterHub(
        ReporterHubArgs(
            reporters=action_reporters,
        )
    )
    reporter_monitor = ReporterMonitor(reporter_hub)
    prometheus_monitor = PrometheusMonitor()
    audit_log_monitor = AuditLogMonitor(root_ctx.db)
    root_ctx.processors = Processors.create(
        ProcessorArgs(
            service_args=ServiceArgs(
                db=root_ctx.db,
                repositories=root_ctx.repositories,
                etcd=root_ctx.etcd,
                config_provider=root_ctx.config_provider,
                storage_manager=root_ctx.storage_manager,
                valkey_stat_client=root_ctx.valkey_stat,
                valkey_live=root_ctx.valkey_live,
                event_fetcher=root_ctx.event_fetcher,
                background_task_manager=root_ctx.background_task_manager,
                event_hub=root_ctx.event_hub,
                agent_registry=root_ctx.registry,
                error_monitor=root_ctx.error_monitor,
                idle_checker_host=root_ctx.idle_checker_host,
                event_dispatcher=root_ctx.event_dispatcher,
                hook_plugin_ctx=root_ctx.hook_plugin_ctx,
                scheduling_controller=root_ctx.scheduling_controller,
                deployment_controller=root_ctx.deployment_controller,
                event_producer=root_ctx.event_producer,
                agent_cache=root_ctx.agent_cache,
            )
        ),
        [reporter_monitor, prometheus_monitor, audit_log_monitor],
    )
    yield


@actxmgr
async def distributed_lock_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.distributed_lock_factory = init_lock_factory(root_ctx)
    yield


@actxmgr
async def event_hub_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.event_hub = EventHub()
    yield
    await root_ctx.event_hub.shutdown()


@actxmgr
async def service_discovery_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    sd_type = root_ctx.config_provider.config.service_discovery.type
    match sd_type:
        case ServiceDiscoveryType.ETCD:
            root_ctx.service_discovery = ETCDServiceDiscovery(
                ETCDServiceDiscoveryArgs(root_ctx.etcd)
            )
        case ServiceDiscoveryType.REDIS:
            live_valkey_target = root_ctx.valkey_profile_target.profile_target(RedisRole.LIVE)
            root_ctx.service_discovery = await RedisServiceDiscovery.create(
                RedisServiceDiscoveryArgs(valkey_target=live_valkey_target)
            )

    root_ctx.sd_loop = ServiceDiscoveryLoop(
        sd_type,
        root_ctx.service_discovery,
        ServiceMetadata(
            display_name=f"manager-{root_ctx.config_provider.config.manager.id}",
            service_group="manager",
            version=__version__,
            endpoint=ServiceEndpoint(
                address=root_ctx.config_provider.config.manager.announce_addr.address,
                port=root_ctx.config_provider.config.manager.announce_addr.port,
                protocol="http",
                prometheus_address=root_ctx.config_provider.config.manager.announce_internal_addr.address,
            ),
        ),
    )

    if root_ctx.config_provider.config.otel.enabled:
        meta = root_ctx.sd_loop.metadata
        otel_spec = OpenTelemetrySpec(
            service_id=meta.id,
            service_name=meta.service_group,
            service_version=meta.version,
            log_level=root_ctx.config_provider.config.otel.log_level,
            endpoint=root_ctx.config_provider.config.otel.endpoint,
        )
        BraceStyleAdapter.apply_otel(otel_spec)
    yield
    root_ctx.sd_loop.close()


@actxmgr
async def message_queue_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.message_queue = await _make_message_queue(root_ctx)
    yield
    await root_ctx.message_queue.close()


@actxmgr
async def event_producer_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.event_fetcher = EventFetcher(root_ctx.message_queue)
    root_ctx.event_producer = EventProducer(
        root_ctx.message_queue,
        source=AGENTID_MANAGER,
        log_events=root_ctx.config_provider.config.debug.log_events,
    )
    yield
    await root_ctx.event_producer.close()
    await asyncio.sleep(0.2)


@actxmgr
async def event_dispatcher_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .event_dispatcher.dispatch import DispatcherArgs, Dispatchers

    root_ctx.event_dispatcher = EventDispatcher(
        root_ctx.message_queue,
        log_events=root_ctx.config_provider.config.debug.log_events,
        event_observer=root_ctx.metrics.event,
    )
    dispatchers = Dispatchers(
        DispatcherArgs(
            root_ctx.valkey_container_log,
            root_ctx.valkey_stat,
            root_ctx.valkey_stream,
            root_ctx.scheduler_dispatcher,
            root_ctx.sokovan_orchestrator.coordinator,
            root_ctx.scheduling_controller,
            root_ctx.sokovan_orchestrator.deployment_coordinator,
            root_ctx.sokovan_orchestrator.route_coordinator,
            root_ctx.repositories.scheduler.repository,
            root_ctx.event_hub,
            root_ctx.registry,
            root_ctx.db,
            root_ctx.idle_checker_host,
            root_ctx.event_dispatcher_plugin_ctx,
            root_ctx.repositories,
            lambda: root_ctx.processors,
            root_ctx.storage_manager,
            root_ctx.config_provider,
            use_sokovan=root_ctx.config_provider.config.manager.use_sokovan,
        )
    )
    dispatchers.dispatch(root_ctx.event_dispatcher)
    await root_ctx.event_dispatcher.start()
    yield
    await root_ctx.event_dispatcher.close()


async def _make_message_queue(
    root_ctx: RootContext,
) -> AbstractMessageQueue:
    redis_profile_target = root_ctx.config_provider.config.redis.to_redis_profile_target()
    stream_redis_target = redis_profile_target.profile_target(RedisRole.STREAM)
    node_id = root_ctx.config_provider.config.manager.id
    args = RedisMQArgs(
        anycast_stream_key="events",
        broadcast_channel="events_all",
        consume_stream_keys={
            "events",
        },
        subscribe_channels={
            "events_all",
        },
        group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
        node_id=node_id,
        db=REDIS_STREAM_DB,
    )
    if root_ctx.config_provider.config.manager.use_experimental_redis_event_dispatcher:
        return HiRedisQueue(
            stream_redis_target,
            args,
        )
    return await RedisQueue.create(
        stream_redis_target,
        args,
    )


@actxmgr
async def idle_checker_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .idle import init_idle_checkers

    root_ctx.idle_checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.config_provider,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await root_ctx.idle_checker_host.start()
    yield
    await root_ctx.idle_checker_host.shutdown()


@actxmgr
async def storage_manager_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .models.storage import StorageSessionManager

    root_ctx.storage_manager = StorageSessionManager(root_ctx.config_provider.config.volumes)
    yield
    await root_ctx.storage_manager.aclose()


@actxmgr
async def repositories_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .repositories.repositories import Repositories
    from .repositories.types import RepositoryArgs

    repositories = Repositories.create(
        args=RepositoryArgs(
            db=root_ctx.db,
            storage_manager=root_ctx.storage_manager,
            config_provider=root_ctx.config_provider,
            valkey_stat_client=root_ctx.valkey_stat,
            valkey_live_client=root_ctx.valkey_live,
            valkey_schedule_client=root_ctx.valkey_schedule,
            valkey_image_client=root_ctx.valkey_image,
        )
    )
    root_ctx.repositories = repositories
    yield


@actxmgr
async def network_plugin_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .plugin.network import NetworkPluginContext

    ctx = NetworkPluginContext(
        root_ctx.etcd,
        root_ctx.config_provider.config.model_dump(by_alias=True),
    )
    root_ctx.network_plugin_ctx = ctx
    await ctx.init(
        context=root_ctx,
        allowlist=root_ctx.config_provider.config.manager.allowed_plugins,
        blocklist=root_ctx.config_provider.config.manager.disabled_plugins,
    )
    log.info("NetworkPluginContext initialized with plugins: {}", list(ctx.plugins.keys()))
    yield
    await ctx.cleanup()


@actxmgr
async def hook_plugin_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    ctx = HookPluginContext(
        root_ctx.etcd,
        root_ctx.config_provider.config.model_dump(by_alias=True),
    )
    root_ctx.hook_plugin_ctx = ctx
    await ctx.init(
        context=root_ctx,
        allowlist=root_ctx.config_provider.config.manager.allowed_plugins,
        blocklist=root_ctx.config_provider.config.manager.disabled_plugins,
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
async def event_dispatcher_plugin_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    ctx = EventDispatcherPluginContext(
        root_ctx.etcd,
        root_ctx.config_provider.config.model_dump(by_alias=True),
    )
    root_ctx.event_dispatcher_plugin_ctx = ctx
    await ctx.init(
        context=root_ctx,
        allowlist=root_ctx.config_provider.config.manager.allowed_plugins,
        blocklist=root_ctx.config_provider.config.manager.disabled_plugins,
    )
    yield
    await ctx.cleanup()


@actxmgr
async def agent_registry_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from zmq.auth.certs import load_certificate

    from ai.backend.manager.sokovan.scheduling_controller import (
        SchedulingController,
        SchedulingControllerArgs,
    )

    from .agent_cache import AgentRPCCache
    from .registry import AgentRegistry

    # Create scheduling controller first
    root_ctx.scheduling_controller = SchedulingController(
        SchedulingControllerArgs(
            repository=root_ctx.repositories.scheduler.repository,
            config_provider=root_ctx.config_provider,
            storage_manager=root_ctx.storage_manager,
            event_producer=root_ctx.event_producer,
            valkey_schedule=root_ctx.valkey_schedule,
            network_plugin_ctx=root_ctx.network_plugin_ctx,
            hook_plugin_ctx=root_ctx.hook_plugin_ctx,
        )
    )
    # Create deployment controller
    root_ctx.deployment_controller = DeploymentController(
        DeploymentControllerArgs(
            scheduling_controller=root_ctx.scheduling_controller,
            deployment_repository=root_ctx.repositories.deployment.repository,
            config_provider=root_ctx.config_provider,
            storage_manager=root_ctx.storage_manager,
            event_producer=root_ctx.event_producer,
            valkey_schedule=root_ctx.valkey_schedule,
        )
    )
    root_ctx.route_controller = RouteController(
        RouteControllerArgs(
            valkey_schedule=root_ctx.valkey_schedule,
        )
    )
    manager_pkey, manager_skey = load_certificate(
        root_ctx.config_provider.config.manager.rpc_auth_manager_keypair
    )
    assert manager_skey is not None
    manager_public_key = PublicKey(manager_pkey)
    manager_secret_key = SecretKey(manager_skey)
    root_ctx.agent_cache = AgentRPCCache(root_ctx.db, manager_public_key, manager_secret_key)
    root_ctx.registry = AgentRegistry(
        root_ctx.config_provider,
        root_ctx.db,
        root_ctx.agent_cache,
        root_ctx.valkey_stat,
        root_ctx.valkey_live,
        root_ctx.valkey_image,
        root_ctx.event_producer,
        root_ctx.event_hub,
        root_ctx.storage_manager,
        root_ctx.hook_plugin_ctx,
        root_ctx.network_plugin_ctx,
        root_ctx.scheduling_controller,
        debug=root_ctx.config_provider.config.debug.enabled,
        manager_public_key=manager_public_key,
        manager_secret_key=manager_secret_key,
        use_sokovan=root_ctx.config_provider.config.manager.use_sokovan,
    )
    await root_ctx.registry.init()
    yield
    await root_ctx.registry.shutdown()


@actxmgr
async def sched_dispatcher_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .scheduler.dispatcher import SchedulerDispatcher

    root_ctx.scheduler_dispatcher = await SchedulerDispatcher.create(
        root_ctx.config_provider,
        root_ctx.etcd,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
        root_ctx.registry,
        root_ctx.valkey_live,
        root_ctx.valkey_stat,
        root_ctx.repositories.schedule.repository,
    )
    yield
    await root_ctx.scheduler_dispatcher.close()


@actxmgr
async def leader_election_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Initialize leader election for distributed coordination."""
    import socket

    from ai.backend.common.clients.valkey_client.valkey_leader.client import ValkeyLeaderClient
    from ai.backend.common.leader import ValkeyLeaderElection, ValkeyLeaderElectionConfig
    from ai.backend.common.leader.tasks import EventProducerTask, LeaderCron, PeriodicTask

    # Create ValkeyLeaderClient for leader election
    valkey_leader_client = await ValkeyLeaderClient.create(
        valkey_target=root_ctx.valkey_profile_target.profile_target(RedisRole.STREAM),
        db_id=REDIS_STREAM_LOCK,  # Use a dedicated DB for leader election
        human_readable_name="leader",
    )

    # Create leader election configuration
    server_id = f"manager-{socket.gethostname()}-{root_ctx.pidx}"
    leader_config = ValkeyLeaderElectionConfig(
        server_id=server_id,
        leader_key="leader:sokovan:scheduler",
        lease_duration=30,
        renewal_interval=10.0,
        failure_threshold=3,
    )

    # Create leader election instance
    root_ctx.leader_election = ValkeyLeaderElection(
        leader_client=valkey_leader_client,
        config=leader_config,
    )

    # Get task specifications from sokovan and register them
    task_specs = root_ctx.sokovan_orchestrator.create_task_specs()

    # Rescan reservoir registry periodically
    task_specs.append(
        EventTaskSpec(
            name="reservoir_registry_scan",
            event_factory=lambda: DoScanReservoirRegistryEvent(),
            interval=3600,  # 1 hour
            initial_delay=0,
        )
    )

    # Create event producer tasks from specs
    leader_tasks: list[PeriodicTask] = [
        EventProducerTask(spec, root_ctx.event_producer) for spec in task_specs
    ]

    # Register tasks with the election system
    leader_cron = LeaderCron(tasks=leader_tasks)
    root_ctx.leader_election.register_task(leader_cron)

    # Start leader election (will start tasks when becoming leader)
    await root_ctx.leader_election.start()
    log.info(f"Leader election started for server {server_id}")

    yield

    # Cleanup leader election
    await root_ctx.leader_election.stop()


@actxmgr
async def sokovan_orchestrator_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .clients.agent import AgentPool
    from .sokovan.scheduler.factory import create_default_scheduler
    from .sokovan.sokovan import SokovanOrchestrator

    # Create agent pool for scheduler
    agent_pool = AgentPool(root_ctx.agent_cache)

    # Create scheduler with default components
    scheduler = create_default_scheduler(
        root_ctx.repositories.scheduler.repository,
        root_ctx.repositories.deployment.repository,
        root_ctx.config_provider,
        root_ctx.distributed_lock_factory,
        agent_pool,
        root_ctx.network_plugin_ctx,
        root_ctx.event_producer,
        root_ctx.valkey_schedule,
    )

    # Create HTTP client pool for deployment operations
    from ai.backend.common.clients.http_client.client_pool import (
        ClientPool,
        tcp_client_session_factory,
    )
    from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
    from ai.backend.manager.sokovan.deployment.route.coordinator import RouteCoordinator

    client_pool = ClientPool(tcp_client_session_factory)

    # Create deployment coordinator
    deployment_coordinator = DeploymentCoordinator(
        valkey_schedule=root_ctx.valkey_schedule,
        deployment_controller=root_ctx.deployment_controller,
        deployment_repository=root_ctx.repositories.deployment.repository,
        event_producer=root_ctx.event_producer,
        lock_factory=root_ctx.distributed_lock_factory,
        config_provider=root_ctx.config_provider,
        scheduling_controller=root_ctx.scheduling_controller,
        client_pool=client_pool,
        valkey_stat=root_ctx.valkey_stat,
        route_controller=root_ctx.route_controller,
    )

    # Create route coordinator
    route_coordinator = RouteCoordinator(
        valkey_schedule=root_ctx.valkey_schedule,
        deployment_repository=root_ctx.repositories.deployment.repository,
        event_producer=root_ctx.event_producer,
        lock_factory=root_ctx.distributed_lock_factory,
        config_provider=root_ctx.config_provider,
        scheduling_controller=root_ctx.scheduling_controller,
        client_pool=client_pool,
    )

    # Create sokovan orchestrator with lock factory for timers
    root_ctx.sokovan_orchestrator = SokovanOrchestrator(
        scheduler=scheduler,
        event_producer=root_ctx.event_producer,
        valkey_schedule=root_ctx.valkey_schedule,
        lock_factory=root_ctx.distributed_lock_factory,
        scheduling_controller=root_ctx.scheduling_controller,
        deployment_coordinator=deployment_coordinator,
        route_coordinator=route_coordinator,
    )

    log.info("Sokovan orchestrator initialized")

    try:
        yield
    finally:
        # Leader election will handle task cleanup
        pass


@actxmgr
async def monitoring_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .plugin.monitor import ManagerErrorPluginContext, ManagerStatsPluginContext

    ectx = ManagerErrorPluginContext(
        root_ctx.etcd, root_ctx.config_provider.config.model_dump(by_alias=True)
    )
    sctx = ManagerStatsPluginContext(
        root_ctx.etcd, root_ctx.config_provider.config.model_dump(by_alias=True)
    )
    init_success = False

    try:
        await ectx.init(
            context={"_root.context": root_ctx},
            allowlist=root_ctx.config_provider.config.manager.allowed_plugins,
        )
        await sctx.init(allowlist=root_ctx.config_provider.config.manager.allowed_plugins)
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


@actxmgr
async def services_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .service.base import ServicesContext
    from .service.container_registry.base import PerProjectRegistryQuotaRepository
    from .service.container_registry.harbor import (
        PerProjectContainerRegistryQuotaClientPool,
        PerProjectContainerRegistryQuotaService,
    )

    db = root_ctx.db

    per_project_container_registries_quota = PerProjectContainerRegistryQuotaService(
        repository=PerProjectRegistryQuotaRepository(db),
        client_pool=PerProjectContainerRegistryQuotaClientPool(),
    )

    root_ctx.services_ctx = ServicesContext(
        per_project_container_registries_quota,
    )
    yield None


class background_task_ctx:
    def __init__(self, root_ctx: RootContext) -> None:
        self.root_ctx = root_ctx

    async def __aenter__(self) -> None:
        self.root_ctx.background_task_manager = BackgroundTaskManager(
            self.root_ctx.event_producer,
            valkey_client=self.root_ctx.valkey_bgtask,
            server_id=self.root_ctx.config_provider.config.manager.id,
            bgtask_observer=self.root_ctx.metrics.bgtask,
        )

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
    global_middlewares: Iterable[Middleware],
) -> None:
    subapp.on_response_prepare.append(on_prepare)

    async def _set_root_ctx(subapp: web.Application):
        # Allow subapp's access to the root app properties.
        # These are the public APIs exposed to plugins as well.
        subapp["_root.context"] = root_app["_root.context"]
        subapp["_root_app"] = root_app

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


def init_lock_factory(root_ctx: RootContext) -> DistributedLockFactory:
    ipc_base_path = root_ctx.config_provider.config.manager.ipc_base_path
    manager_id = root_ctx.config_provider.config.manager.id
    lock_backend = root_ctx.config_provider.config.manager.distributed_lock
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

            redlock_config = root_ctx.config_provider.config.manager.redlock_config
            redis_profile_target = root_ctx.config_provider.config.redis.to_redis_profile_target()
            redis_lock = redis_helper.get_redis_object(
                redis_profile_target.profile_target(RedisRole.STREAM_LOCK),
                name="lock",  # distributed locks
                db=REDIS_STREAM_LOCK,
            )
            return lambda lock_id, lifetime_hint: RedisLock(
                str(lock_id),
                redis_lock,
                lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
                lock_retry_interval=redlock_config["lock_retry_interval"],
            )
        case "etcd":
            from ai.backend.common.lock import EtcdLock

            return lambda lock_id, lifetime_hint: EtcdLock(
                str(lock_id),
                root_ctx.etcd,
                lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
            )
        case other:
            raise ValueError(f"Invalid lock backend: {other}")


def build_root_app(
    pidx: int,
    bootstrap_config: BootstrapConfig,
    *,
    cleanup_contexts: Optional[Sequence[CleanupContext]] = None,
    subapp_pkgs: Optional[Sequence[str]] = None,
    scheduler_opts: Optional[Mapping[str, Any]] = None,
) -> web.Application:
    from .sweeper.kernel import stale_kernel_sweeper_ctx
    from .sweeper.session import stale_session_sweeper_ctx

    public_interface_objs.clear()
    if bootstrap_config.pyroscope.enabled:
        if (
            not bootstrap_config.pyroscope.app_name
            or not bootstrap_config.pyroscope.server_addr
            or not bootstrap_config.pyroscope.sample_rate
        ):
            raise ValueError("Pyroscope configuration is incomplete.")

        Profiler(
            pyroscope_args=PyroscopeArgs(
                enabled=bootstrap_config.pyroscope.enabled,
                application_name=bootstrap_config.pyroscope.app_name,
                server_address=bootstrap_config.pyroscope.server_addr,
                sample_rate=bootstrap_config.pyroscope.sample_rate,
            )
        )

    root_ctx = RootContext()
    root_ctx.metrics = CommonMetricRegistry.instance()
    app = web.Application(
        middlewares=[
            request_id_middleware,
            exception_middleware,
            api_middleware,
            build_api_metric_middleware(root_ctx.metrics.api),
        ]
    )
    global_exception_handler = functools.partial(handle_loop_error, root_ctx)
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(global_exception_handler)
    app["_root.context"] = root_ctx

    # If the request path starts with the following route, the auth_middleware is bypassed.
    # In this case, all authentication flags are turned off.
    # Used in special cases where the request headers cannot be modified.
    app["auth_middleware_allowlist"] = [
        "/container-registries/webhook",
    ]

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
        "agent_selection_strategy": AgentSelectionStrategy.DISPERSED,
    }
    app["scheduler_opts"] = {
        **default_scheduler_opts,
        **(scheduler_opts if scheduler_opts is not None else {}),
    }
    app.on_response_prepare.append(on_prepare)

    if cleanup_contexts is None:
        cleanup_contexts = [
            event_hub_ctx,
            manager_status_ctx,
            redis_ctx,
            database_ctx,
            services_ctx,
            distributed_lock_ctx,
            message_queue_ctx,
            event_producer_ctx,
            storage_manager_ctx,
            repositories_ctx,
            hook_plugin_ctx,
            monitoring_ctx,
            network_plugin_ctx,
            event_dispatcher_plugin_ctx,
            idle_checker_ctx,
            agent_registry_ctx,
            sched_dispatcher_ctx,
            sokovan_orchestrator_ctx,
            leader_election_ctx,
            event_dispatcher_ctx,
            background_task_ctx,
            stale_session_sweeper_ctx,
            stale_kernel_sweeper_ctx,
            processors_ctx,
            service_discovery_ctx,
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

    vendor_path = importlib.resources.files("ai.backend.manager.vendor")
    assert isinstance(vendor_path, Path)
    app.router.add_static("/static/vendor", path=vendor_path, name="static")
    return app


def build_prometheus_service_discovery_handler(
    root_ctx: RootContext,
) -> Handler:
    async def _handler(request: web.Request) -> web.Response:
        services = await root_ctx.service_discovery.discover()
        resp = []
        for service in services:
            resp.append({
                "targets": [f"{service.endpoint.prometheus_address}"],
                "labels": {
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


def build_internal_app(root_ctx: RootContext) -> web.Application:
    app = web.Application()
    metric_registry = CommonMetricRegistry.instance()
    app.router.add_route("GET", r"/metrics", build_prometheus_metrics_handler(metric_registry))
    app.router.add_route(
        "GET", r"/metrics/service_discovery", build_prometheus_service_discovery_handler(root_ctx)
    )
    return app


def build_public_app(
    root_ctx: RootContext,
    subapp_pkgs: Iterable[str] | None = None,
) -> web.Application:
    app = web.Application()
    app["_root.context"] = root_ctx
    if subapp_pkgs is None:
        subapp_pkgs = []
    for pkg_name in subapp_pkgs:
        if root_ctx.pidx == 0:
            log.info("Loading module: {0}", pkg_name[1:])
        subapp_mod = importlib.import_module(pkg_name, "ai.backend.manager.public_api")
        init_subapp(pkg_name, app, getattr(subapp_mod, "create_app"))
    return app


@dataclass
class ServerMainArgs:
    bootstrap_cfg: BootstrapConfig
    bootstrap_cfg_path: Path
    log_endpoint: str
    log_level: LogLevel


@actxmgr
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    args: ServerMainArgs,
) -> AsyncIterator[None]:
    boostrap_config = args.bootstrap_cfg

    root_app = build_root_app(pidx, boostrap_config, subapp_pkgs=global_subapp_pkgs)
    root_ctx: RootContext = root_app["_root.context"]
    internal_app = build_internal_app(root_ctx)

    # Start aiomonitor.
    # Port is set by config (default=50100 + pidx).
    loop.set_debug(boostrap_config.debug.asyncio)
    m = aiomonitor.Monitor(
        loop,
        termui_port=boostrap_config.manager.aiomonitor_termui_port + pidx,
        webui_port=boostrap_config.manager.aiomonitor_webui_port + pidx,
        console_enabled=False,
        hook_task_factory=boostrap_config.debug.enhanced_aiomonitor_task_info,
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
            etcd_ctx(root_ctx, boostrap_config.etcd.to_dataclass()),
            config_provider_ctx(root_ctx, args.log_level, args.bootstrap_cfg_path),
            webapp_plugin_ctx(root_app),
        ):
            ssl_ctx = None
            if root_ctx.config_provider.config.manager.ssl_enabled:
                ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_ctx.load_cert_chain(
                    str(root_ctx.config_provider.config.manager.ssl_cert),
                    root_ctx.config_provider.config.manager.ssl_privkey,
                )

            runner = web.AppRunner(root_app, keepalive_timeout=30.0)
            internal_runner = web.AppRunner(internal_app, keepalive_timeout=30.0)
            await runner.setup()
            await internal_runner.setup()
            service_addr = root_ctx.config_provider.config.manager.service_addr
            internal_addr = root_ctx.config_provider.config.manager.internal_addr
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
            public_metrics_port = root_ctx.config_provider.config.manager.public_metrics_port
            if public_metrics_port is not None:
                _app = build_public_app(
                    root_ctx, subapp_pkgs=global_subapp_pkgs_for_public_metrics_app
                )
                _runner = web.AppRunner(_app, keepalive_timeout=30.0)
                await _runner.setup()
                _site = web.TCPSite(
                    _runner,
                    service_addr.host,
                    public_metrics_port,
                    backlog=1024,
                    reuse_port=True,
                )
                await _site.start()
                log.info(
                    f"started handling public metric API requests at {service_addr.host}:{public_metrics_port}"
                )

            if os.geteuid() == 0:
                uid = root_ctx.config_provider.config.manager.user
                gid = root_ctx.config_provider.config.manager.group
                if uid is None or gid is None:
                    raise ValueError("user/group must be specified when running as root")

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
    config_path: Optional[Path],
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
                if bootstrap_cfg.manager.event_loop == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                try:
                    aiotools.start_server(
                        server_main_logwrapper,
                        num_workers=bootstrap_cfg.manager.num_proc,
                        args=(bootstrap_cfg, discovered_cfg_path, log_endpoint, log_level),
                        wait_timeout=5.0,
                    )
                finally:
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
