from __future__ import annotations

import asyncio
import functools
import grp
import importlib
import importlib.resources
import ipaddress
import logging
import os
import pwd
import ssl
import sys
import time
import traceback
import uuid
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator, Final, Iterable, Mapping, Sequence, cast
from uuid import UUID

import aiohttp_cors
import aiohttp_jinja2
import aiomonitor
import aiotools
import click
import jinja2
import memray
import pyroscope
from aiohttp import web
from pydantic import ValidationError
from setproctitle import setproctitle

from ai.backend.appproxy.common.config import RedisConfig
from ai.backend.appproxy.common.defs import (
    AGENTID_COORDINATOR,
    APPPROXY_ANYCAST_STREAM_KEY,
    APPPROXY_BROADCAST_CHANNEL,
)
from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.common.events import (
    DoCheckUnusedPortEvent,
    WorkerLostEvent,
)
from ai.backend.appproxy.common.exceptions import (
    BackendError,
    GenericBadRequest,
    GenericForbidden,
    InternalServerError,
    MethodNotAllowed,
    ObjectNotFound,
    URLNotFound,
)
from ai.backend.appproxy.common.types import (
    AppCreator,
    AppMode,
    HealthCheckConfig,
    ProxyProtocol,
    RouteInfo,
    WebMiddleware,
    WebRequestHandler,
)
from ai.backend.appproxy.common.utils import (
    BackendAIAccessLogger,
    ensure_json_serializable,
    mime_match,
    ping_redis_connection,
)
from ai.backend.appproxy.coordinator.models.worker import WorkerStatus
from ai.backend.common import redis_helper
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.defs import REDIS_LIVE_DB, REDIS_STREAM_DB, REDIS_STREAM_LOCK, RedisRole
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.etcd import ConfigScopes
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.events.event_types.model_serving.anycast import (
    EndpointRouteListUpdatedEvent,
)
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.metrics.http import build_api_metric_middleware
from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
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
    AgentId,
    HostPortPair,
    ModelServiceStatus,
    RedisProfileTarget,
    ServiceDiscoveryType,
)
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel
from ai.backend.logging.otel import OpenTelemetrySpec

from . import __version__
from .config import ServerConfig
from .config import load as load_config
from .defs import EVENT_DISPATCHER_CONSUMER_GROUP, LockID
from .models import Circuit, Endpoint, Worker
from .models.utils import execute_with_txn_retry
from .types import (
    CircuitManager,
    CleanupContext,
    CoordinatorMetricRegistry,
    DistributedLockFactory,
    InferenceAppConfigDict,
    RootContext,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

global_subapp_pkgs: Final[list[str]] = [
    ".circuit_v1",
    ".circuit_v2",
    ".conf",
    ".endpoint",
    ".health",
    ".proxy",
    ".slot_v1",
    ".slot_v2",
    ".worker_v1",
    ".worker_v2",
]


@web.middleware
async def request_context_aware_middleware(
    request: web.Request, handler: WebRequestHandler
) -> web.StreamResponse:
    request_id = request.headers.get("X-BackendAI-RequestID", str(uuid.uuid4()))
    request["request_id"] = request_id
    if _current_task := asyncio.current_task():
        setattr(_current_task, "request_id", request_id)
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
    resp = await _handler(request)
    return resp


@web.middleware
async def exception_middleware(
    request: web.Request, handler: WebRequestHandler
) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    try:
        resp = await handler(request)
    except ValidationError as ex:
        log.exception("Failed to create response model: {}", ex.json(indent=2))
        raise InternalServerError()
    except BackendError as ex:
        if ex.status_code == 500:
            log.warning("Internal server error raised inside handlers")
        log.exception("")
        if mime_match(request.headers.get("accept", "text/html"), "application/json"):
            return web.json_response(
                ensure_json_serializable(ex.body_dict),
                status=ex.status_code,
                headers={"Access-Control-Allow-Origin": "*"},
            )
        else:
            return aiohttp_jinja2.render_template(
                "error",
                request,
                ex.body_dict,
                status=ex.status_code,
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
async def redis_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    redis_profile_target = RedisProfileTarget.from_dict(root_ctx.local_config.redis.to_dict())
    core_redis_profile_target = RedisProfileTarget.from_dict(
        (root_ctx.local_config.core_redis or root_ctx.local_config.redis).to_dict()
    )

    # Create valkey clients for live data access
    root_ctx.valkey_live = await ValkeyLiveClient.create(
        valkey_target=redis_profile_target.profile_target(RedisRole.LIVE).to_valkey_target(),
        db_id=REDIS_LIVE_DB,
        human_readable_name="appproxy-coordinator-live",
    )
    root_ctx.core_valkey_live = await ValkeyLiveClient.create(
        valkey_target=core_redis_profile_target.profile_target(RedisRole.LIVE).to_valkey_target(),
        db_id=REDIS_LIVE_DB,
        human_readable_name="appproxy-coordinator-core-live",
    )

    # Keep redis_lock for distributed locking (not yet migrated)
    root_ctx.redis_lock = redis_helper.get_redis_object(
        redis_profile_target.profile_target(RedisRole.STREAM),
        name="lock",  # distributed locks
        db=REDIS_STREAM_LOCK,
    )
    await ping_redis_connection(root_ctx.redis_lock)

    # Initialize ValkeyScheduleClient for health status updates
    root_ctx.valkey_schedule = await ValkeyScheduleClient.create(
        valkey_target=core_redis_profile_target.profile_target(RedisRole.STREAM).to_valkey_target(),
        db_id=REDIS_LIVE_DB,
        human_readable_name="appproxy-schedule",
    )
    log.info("ValkeyScheduleClient initialized for health status updates")

    yield

    await root_ctx.valkey_live.close()
    await root_ctx.core_valkey_live.close()
    await root_ctx.valkey_schedule.close()
    await root_ctx.redis_lock.close()


async def _make_message_queue(
    node_id: str,
    redis_config: RedisConfig,
    *,
    anycast_stream_key=APPPROXY_ANYCAST_STREAM_KEY,
    broadcast_channel=APPPROXY_BROADCAST_CHANNEL,
    use_experimental_redis_event_dispatcher: bool = False,
) -> AbstractMessageQueue:
    redis_profile_target: RedisProfileTarget = RedisProfileTarget.from_dict(redis_config.to_dict())
    stream_redis_target = redis_profile_target.profile_target(RedisRole.STREAM)

    args = RedisMQArgs(
        anycast_stream_key=anycast_stream_key,
        broadcast_channel=broadcast_channel,
        consume_stream_keys={
            anycast_stream_key,
        },
        subscribe_channels={
            broadcast_channel,
        },
        group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
        node_id=node_id,
        db=REDIS_STREAM_DB,
    )

    if use_experimental_redis_event_dispatcher:
        return HiRedisQueue(
            stream_redis_target,
            args,
        )
    else:
        return await RedisQueue.create(
            stream_redis_target,
            args,
        )


@actxmgr
async def event_dispatcher_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    mq = await _make_message_queue(
        root_ctx.local_config.proxy_coordinator.id,
        root_ctx.local_config.redis,
        use_experimental_redis_event_dispatcher=root_ctx.local_config.proxy_coordinator.use_experimental_redis_event_dispatcher,
    )
    root_ctx.event_producer = EventProducer(
        mq,
        source=AGENTID_COORDINATOR,
        log_events=root_ctx.local_config.debug.log_events,
    )
    root_ctx.event_dispatcher = EventDispatcher(
        mq,
        log_events=root_ctx.local_config.debug.log_events,
        event_observer=root_ctx.metrics.event,
    )
    core_mq = await _make_message_queue(
        root_ctx.local_config.proxy_coordinator.id,
        root_ctx.local_config.core_redis or root_ctx.local_config.redis,
        anycast_stream_key="events",
        broadcast_channel="events_all",
        use_experimental_redis_event_dispatcher=root_ctx.local_config.proxy_coordinator.use_experimental_redis_event_dispatcher,
    )
    root_ctx.core_event_producer = EventProducer(
        core_mq,
        source=AGENTID_COORDINATOR,
        log_events=root_ctx.local_config.debug.log_events,
    )
    root_ctx.core_event_dispatcher = EventDispatcher(
        core_mq,
        log_events=root_ctx.local_config.debug.log_events,
        event_observer=root_ctx.metrics.event,
    )
    await root_ctx.event_dispatcher.start()
    await root_ctx.core_event_dispatcher.start()

    yield

    await root_ctx.event_producer.close()
    await root_ctx.core_event_producer.close()
    await asyncio.sleep(0.2)


@actxmgr
async def etcd_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    if root_ctx.local_config.proxy_coordinator.enable_traefik:
        traefik_config = root_ctx.local_config.proxy_coordinator.traefik
        assert traefik_config

        creds: dict[str, str] | None = None
        if traefik_config.etcd.password:
            creds = {"password": traefik_config.etcd.password}

        root_ctx.traefik_etcd = TraefikEtcd(
            HostPortPair(traefik_config.etcd.addr.host, traefik_config.etcd.addr.port),
            traefik_config.etcd.namespace,
            {ConfigScopes.GLOBAL: ""},
            credentials=creds,
        )
    else:
        root_ctx.traefik_etcd = None
    yield


async def on_worker_lost_event(
    context: RootContext,
    worker_id: AgentId,
    event: WorkerLostEvent,
) -> None:
    log.warning("detected termination of proxy worker {}", event.worker_id)

    async def _update(sess: SASession) -> None:
        try:
            worker = await Worker.find_by_authority(sess, event.worker_id)
            worker.status = WorkerStatus.LOST
            await sess.flush()
        except ObjectNotFound:
            log.warning("worker {} not found in database", event.worker_id)

    async with context.db.connect() as db_conn:
        await execute_with_txn_retry(_update, context.db.begin_session, db_conn)


async def on_route_update_event(
    context: RootContext,
    worker_id: AgentId,
    event: EndpointRouteListUpdatedEvent,
) -> None:
    (
        route_connection_info_json,
        health_check_enabled_str,
        health_check_config_json,
    ) = await context.core_valkey_live.get_multiple_live_data([
        f"endpoint.{event.endpoint_id}.route_connection_info",
        f"endpoint.{event.endpoint_id}.health_check_enabled",
        f"endpoint.{event.endpoint_id}.health_check_config",
    ])
    assert route_connection_info_json, (
        f"EndpointRouteListUpdatedEvent fired but no route info present on redis - expected 'endpoint.{event.endpoint_id}.route_connection_info' key to be present on redis_live"
    )
    assert health_check_enabled_str, (
        f"EndpointRouteListUpdatedEvent fired but no health check info present on redis - expected 'endpoint.{event.endpoint_id}.health_check_enabled' key to be present on redis_live"
    )
    route_connection_info = InferenceAppConfigDict.validate_json(route_connection_info_json)

    health_check_enabled = health_check_enabled_str.decode("utf-8") == "true"
    health_check_config: HealthCheckConfig | None
    if health_check_enabled:
        assert health_check_config_json, (
            f"EndpointRouteListUpdatedEvent fired but invalid health check configuration provided - expected 'endpoint.{event.endpoint_id}.health_check_config' key to be present on redis_live"
        )
        health_check_config = HealthCheckConfig.model_validate_json(
            health_check_config_json.decode("utf-8")
        )
    else:
        health_check_config = None

    app_names = list(route_connection_info.keys())
    if len(app_names) > 0:
        app = app_names[0]
        new_routes = {r.session_id: RouteInfo(**r.model_dump()) for r in route_connection_info[app]}
    else:
        app = ""
        new_routes = {}

    async def _update(db_sess: SASession) -> None:
        endpoint = await Endpoint.get(db_sess, event.endpoint_id)
        circuit = await Circuit.get_by_endpoint(db_sess, endpoint.id)
        old_routes = circuit.route_info or []
        if new_routes:
            traffic_ratios = await context.core_valkey_live.get_multiple_live_data([
                f"endpoint.{event.endpoint_id}.session.{route.session_id}.traffic_ratio"
                for route in new_routes.values()
            ])
            for idx, route in enumerate(new_routes.values()):
                ratio_bytes = traffic_ratios[idx]
                route.traffic_ratio = float(ratio_bytes.decode("utf-8")) if ratio_bytes else 1.0
            for route in old_routes:
                if _duplicate_route := new_routes.get(route.session_id):
                    _duplicate_route.health_status = route.health_status
                    _duplicate_route.last_health_check = route.last_health_check
                    _duplicate_route.consecutive_failures = route.consecutive_failures
        circuit.route_info = list(new_routes.values())

        endpoint.health_check_enabled = health_check_enabled
        endpoint.health_check_config = health_check_config

        await db_sess.commit()

        if not endpoint.health_check_enabled:
            # mark all routes as healthy
            # Publish health status transition events
            await context.health_engine.publish_health_transition_events([
                (r.session_id, None, ModelServiceStatus.HEALTHY) for r in circuit.route_info
            ])

        # Propagate updated route information to AppProxy workers
        await context.health_engine.propagate_route_updates_to_workers(circuit, old_routes)

    async with context.db.connect() as db_conn:
        await execute_with_txn_retry(_update, context.db.begin_session, db_conn)


@actxmgr
async def event_handler_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    worker_lost_handler = root_ctx.event_dispatcher.consume(
        WorkerLostEvent, root_ctx, on_worker_lost_event, name="proxy-coordinator"
    )
    endpoint_route_update_handler = root_ctx.core_event_dispatcher.consume(
        EndpointRouteListUpdatedEvent,
        root_ctx,
        on_route_update_event,
        name="proxy-coordinator",
    )
    yield
    root_ctx.event_dispatcher.unconsume(worker_lost_handler)
    root_ctx.core_event_dispatcher.unconsume(endpoint_route_update_handler)


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
async def health_check_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..common.events import DoHealthCheckEvent
    from .health_checker import HealthCheckEngine

    health_engine = HealthCheckEngine(
        root_ctx.db,
        root_ctx.core_event_producer,
        root_ctx.valkey_live,
        root_ctx.circuit_manager,
        root_ctx.local_config.proxy_coordinator.health_check_timer_interval,
        root_ctx.valkey_schedule,
    )
    root_ctx.health_engine = health_engine
    await health_engine.start()

    async def _check_health(context: None, src: AgentId, event: DoHealthCheckEvent) -> None:
        try:
            # Check all endpoints with health checking enabled
            # This now only performs individual route health checks
            await health_engine.check_all_endpoints()
            log.debug("Health check cycle completed - individual route health updated")

        except Exception:
            log.exception("Error during health check")
            raise

    health_check_evh = root_ctx.event_dispatcher.consume(
        DoHealthCheckEvent,
        None,
        _check_health,
    )
    health_check_timer = GlobalTimer(
        root_ctx.distributed_lock_factory(LockID.LOCKID_HEALTH_CHECK, 10.0),
        root_ctx.event_producer,
        lambda: DoHealthCheckEvent(),
        root_ctx.local_config.proxy_coordinator.health_check_timer_interval,
        initial_delay=5.0,
        task_name="health_check_task",
    )
    await health_check_timer.join()

    yield

    await health_check_timer.leave()
    root_ctx.event_dispatcher.unconsume(health_check_evh)
    await health_engine.stop()


@actxmgr
async def unused_port_collection_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    async def _collect(context: None, src: AgentId, event: DoCheckUnusedPortEvent) -> None:
        try:

            async def _update(sess: SASession) -> list[Circuit]:
                non_inference_http_circuits = [
                    c
                    for c in (await Circuit.list_circuits(sess))
                    if c.app_mode != AppMode.INFERENCE and c.protocol == ProxyProtocol.HTTP
                ]
                if len(non_inference_http_circuits) == 0:
                    return []
                last_access = await root_ctx.valkey_live.get_multiple_live_data([
                    f"circuit.{str(c.id)}.last_access" for c in non_inference_http_circuits
                ])
                unused_circuits = [
                    non_inference_http_circuits[idx]
                    for idx in range(len(last_access))
                    if (
                        time.time()
                        - (
                            float(last_access[idx].decode("utf-8"))
                            if last_access[idx]
                            else non_inference_http_circuits[idx].created_at.timestamp()
                        )
                    )
                    > root_ctx.local_config.proxy_coordinator.unused_circuit_collection_timeout
                ]
                if len(unused_circuits) == 0:
                    return []

                log.info(
                    "collecting {} unused circuits: {}",
                    len(unused_circuits),
                    [str(c.id) for c in unused_circuits],
                )

                worker_map: dict[UUID, Worker] = {}
                for circuit in unused_circuits:
                    if circuit.worker not in worker_map:
                        worker_map[circuit.worker] = await Worker.get(sess, circuit.worker)

                    worker_map[circuit.worker].occupied_slots -= 1
                    await sess.delete(circuit)

                return unused_circuits

            async with root_ctx.db.connect() as db_conn:
                unused_circuits = await execute_with_txn_retry(
                    _update, root_ctx.db.begin_session, db_conn
                )
            await root_ctx.circuit_manager.unload_circuits(unused_circuits)

        except Exception:
            log.exception("")
            raise

    unused_port_collection_evh = root_ctx.event_dispatcher.consume(
        DoCheckUnusedPortEvent,
        None,
        _collect,
    )
    unused_port_collection_timer = GlobalTimer(
        root_ctx.distributed_lock_factory(LockID.LOCKID_UNUSED_PORT, 10.0),
        root_ctx.event_producer,
        lambda: DoCheckUnusedPortEvent(),
        # this number does not represent inactivity threshold; actual limit value is defined at root_ctx.local_config
        10.0,
        initial_delay=5.0,
        task_name="check_unused_port_task",
    )
    await unused_port_collection_timer.join()

    yield
    await unused_port_collection_timer.leave()
    root_ctx.event_dispatcher.unconsume(unused_port_collection_evh)


@actxmgr
async def service_discovery_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    sd_type = root_ctx.local_config.service_discovery.type
    service_discovery: ServiceDiscovery
    match sd_type:
        case ServiceDiscoveryType.REDIS:
            # Use core redis for service discovery if available, otherwise use main redis
            core_redis_profile_target = RedisProfileTarget.from_dict(
                (root_ctx.local_config.core_redis or root_ctx.local_config.redis).to_dict()
            )
            live_redis_target = core_redis_profile_target.profile_target(RedisRole.LIVE)
            service_discovery = await RedisServiceDiscovery.create(
                RedisServiceDiscoveryArgs(valkey_target=live_redis_target.to_valkey_target())
            )
        case _:
            raise RuntimeError(
                f"Unsupported service discovery type: {sd_type}. "
                "Please use Redis service discovery for appproxy."
            )

    # Determine announce addresses
    announce_addr = root_ctx.local_config.proxy_coordinator.announce_addr
    sd_loop = ServiceDiscoveryLoop(
        sd_type,
        service_discovery,
        ServiceMetadata(
            display_name=f"appproxy-coordinator-{root_ctx.local_config.proxy_coordinator.id}",
            service_group="appproxy-coordinator",
            version=__version__,
            endpoint=ServiceEndpoint(
                address=announce_addr.host,
                port=announce_addr.port,
                protocol="http",
                # It can be separated into an internal-purpose port later.
                prometheus_address=str(announce_addr),
            ),
        ),
    )

    if root_ctx.local_config.otel.enabled:
        meta = sd_loop.metadata
        otel_spec = OpenTelemetrySpec(
            service_id=meta.id,
            service_name=meta.service_group,
            service_version=meta.version,
            log_level=root_ctx.local_config.otel.log_level,
            endpoint=root_ctx.local_config.otel.endpoint,
        )
        BraceStyleAdapter.apply_otel(otel_spec)
    yield
    sd_loop.close()


@actxmgr
async def circuit_manager_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.circuit_manager = CircuitManager(
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.traefik_etcd,
        root_ctx.local_config,
    )
    if root_ctx.local_config.proxy_coordinator.enable_traefik:
        async with root_ctx.db.begin_readonly_session() as session:
            circuits = await Circuit.list_circuits(session, load_worker=True, load_endpoint=True)
            log.info("Injecting traefik configuration of {} circuits", len(circuits))
            await root_ctx.circuit_manager.initialize_traefik_circuits(circuits)

    yield


async def metrics(request: web.Request) -> web.Response:
    request["do_not_print_access_log"] = True
    root_ctx: RootContext = request.app["_root.context"]
    allowed_network = ipaddress.IPv4Network(
        root_ctx.local_config.proxy_coordinator.metric_access_allowed_hosts
    )
    if not request.remote:
        raise GenericForbidden
    try:
        remote_ip = ipaddress.IPv4Network(request.remote)
        if not remote_ip.subnet_of(allowed_network):
            raise GenericForbidden
    except ValueError:
        raise GenericForbidden

    response = web.Response(
        text=root_ctx.metrics.to_prometheus(),
        content_type="text/plain",
    )
    return response


async def on_prepare(request: web.Request, response: web.StreamResponse) -> None:
    response.headers["Server"] = "BackendAI"


async def status(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    request["do_not_print_access_log"] = True
    advertised_addr = root_ctx.local_config.proxy_coordinator.advertised_addr
    if advertised_addr is None:
        return web.json_response({
            "api_version": "v2",
        })
    return web.json_response({
        "api_version": "v2",
        "advertise_address": str(root_ctx.local_config.proxy_coordinator.advertise_base_url),
    })


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
    root_app.middlewares.extend(global_middlewares)  # type: ignore


def init_subapp(pkg_name: str, root_app: web.Application, create_subapp: AppCreator) -> None:
    root_ctx: RootContext = root_app["_root.context"]
    subapp, global_middlewares = create_subapp(root_ctx.cors_options)
    _init_subapp(pkg_name, root_app, subapp, global_middlewares)


def init_lock_factory(root_ctx: RootContext) -> DistributedLockFactory:
    ipc_base_path = root_ctx.local_config.proxy_coordinator.ipc_base_path
    coordinator_id = root_ctx.local_config.proxy_coordinator.id
    lock_backend = root_ctx.local_config.proxy_coordinator.distributed_lock
    log.debug("using {} as the distributed lock backend", lock_backend)
    match lock_backend:
        case "filelock":
            from ai.backend.common.lock import FileLock

            return lambda lock_id, lifetime_hint: FileLock(
                ipc_base_path / f"{coordinator_id}.{lock_id}.lock",
                timeout=0,
            )
        case "pg_advisory":
            from .pglock import PgAdvisoryLock

            return lambda lock_id, lifetime_hint: PgAdvisoryLock(root_ctx.db, lock_id)
        case "redlock":
            from ai.backend.common.lock import RedisLock

            redlock_config = root_ctx.local_config.proxy_coordinator.redlock_config

            return lambda lock_id, lifetime_hint: RedisLock(
                str(lock_id),
                root_ctx.redis_lock,
                lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
                lock_retry_interval=redlock_config.lock_retry_interval,
            )
        case other:
            raise ValueError(f"Invalid lock backend: {other}")


def build_root_app(
    pidx: int,
    local_config: ServerConfig,
    *,
    cleanup_contexts: Sequence[CleanupContext] | None = None,
    subapp_pkgs: Sequence[str] = [],
) -> web.Application:
    root_ctx = RootContext()
    root_ctx.metrics = CoordinatorMetricRegistry.instance()

    app = web.Application(
        middlewares=[
            request_context_aware_middleware,
            exception_middleware,
            api_middleware,
            build_api_metric_middleware(root_ctx.metrics.api),
        ]
    )
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
    with importlib.resources.as_file(importlib.resources.files("ai.backend.appproxy.common")) as f:
        template_path = f / "templates"
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_path))

    if cleanup_contexts is None:
        cleanup_contexts = [
            redis_ctx,
            distributed_lock_ctx,
            database_ctx,
            event_dispatcher_ctx,
            etcd_ctx,
            circuit_manager_ctx,
            health_check_ctx,
            unused_port_collection_ctx,
            event_handler_ctx,
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
    cors.add(app.router.add_route("GET", "/status", status))
    cors.add(app.router.add_route("GET", "/metrics", metrics))
    if subapp_pkgs is None:
        subapp_pkgs = []
    for pkg_name in subapp_pkgs:
        if pidx == 0:
            log.info("Loading module: {0}", pkg_name[1:])
        subapp_mod = importlib.import_module(pkg_name, "ai.backend.appproxy.coordinator.api")
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
        termui_port=root_ctx.local_config.proxy_coordinator.aiomonitor_termui_port + pidx,
        webui_port=root_ctx.local_config.proxy_coordinator.aiomonitor_webui_port + pidx,
        console_enabled=False,
        hook_task_factory=root_ctx.local_config.debug.enhanced_aiomonitor_task_info,
    )
    m.prompt = f"monitor (proxy-coordinator[{pidx}@{os.getpid()}]) >>> "
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
        if root_ctx.local_config.proxy_coordinator.tls_listen:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(
                str(root_ctx.local_config.proxy_coordinator.tls_cert),
                str(root_ctx.local_config.proxy_coordinator.tls_privkey),
            )

        runner = web.AppRunner(
            root_app, keepalive_timeout=30.0, access_log_class=BackendAIAccessLogger
        )
        await runner.setup()
        service_addr = root_ctx.local_config.proxy_coordinator.bind_addr
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
            uid = root_ctx.local_config.proxy_coordinator.user
            gid = root_ctx.local_config.proxy_coordinator.group
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
    _args: tuple[ServerConfig, str],
) -> AsyncIterator[None]:
    setproctitle(f"backend.ai: proxy-coordinator worker-{pidx}")
    local_config: ServerConfig = _args[0]
    log_endpoint: str = _args[1]
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
        sys.stderr.write(traceback.format_exc() + "\n")
        sys.stderr.flush()


@click.group(invoke_without_command=True)
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=Path,
    default=None,
    help=(
        "The config file path. (default: ./proxy-coordinator.toml and"
        " /etc/backend.ai/proxy-coordinator.toml)"
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
def main(ctx: click.Context, config_path: Path, debug: bool, log_level: LogLevel) -> None:
    """
    Start the proxy-coordinator service as a foreground process.
    """
    log_level = LogLevel.DEBUG if debug else log_level
    server_config = load_config(config_path, log_level)

    if ctx.invoked_subcommand is None:
        tracker: memray.Tracker | None = None
        if server_config.profiling.enable_pyroscope:
            assert server_config.profiling.pyroscope_config
            pyroscope.configure(**server_config.profiling.pyroscope_config.model_dump())
        if server_config.profiling.enable_memray:
            tracker = memray.Tracker(
                server_config.profiling.memray_output_destination,
                follow_fork=True,
            )
            tracker.__enter__()
        server_config.proxy_coordinator.pid_file.touch(exist_ok=True)
        server_config.proxy_coordinator.pid_file.write_text(str(os.getpid()))
        ipc_base_path = server_config.proxy_coordinator.ipc_base_path
        ipc_base_path.mkdir(exist_ok=True, parents=True)
        log_sockpath = ipc_base_path / f"coordinator-logger-{os.getpid()}.sock"
        log_endpoint = f"ipc://{log_sockpath}"
        try:
            logger = Logger(
                server_config.logging,
                is_master=True,
                log_endpoint=log_endpoint,
                msgpack_options={
                    "pack_opts": DEFAULT_PACK_OPTS,
                    "unpack_opts": DEFAULT_UNPACK_OPTS,
                },
            )
            with logger:
                setproctitle("backend.ai: proxy-coordinator")
                log.info("Backend.AI AppProxy Coordinator {0}", __version__)
                log.info("runtime: {0}", env_info())
                if server_config.profiling.enable_pyroscope:
                    log.info("Pyroscope tracing enabled")
                if server_config.profiling.enable_memray:
                    log.info("Memray tracing enabled")
                log_config = logging.getLogger("ai.backend.appproxy.coordinator.config")
                log_config.debug("debug mode enabled.")
                if server_config.proxy_coordinator.event_loop == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                try:
                    aiotools.start_server(
                        server_main_logwrapper,  # type: ignore
                        num_workers=1,
                        args=(server_config, log_endpoint),
                        wait_timeout=5.0,
                    )
                finally:
                    log.info("terminated.")
        finally:
            if server_config.proxy_coordinator.pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                server_config.proxy_coordinator.pid_file.unlink()
            if tracker:
                tracker.__exit__(None, None, None)
    else:
        # Click is going to invoke a subcommand.
        pass


if __name__ == "__main__":
    sys.exit(main())
