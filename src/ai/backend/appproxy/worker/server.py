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
import traceback
import uuid
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import Any, AsyncIterator, Final, Iterable, Mapping, Sequence, cast

import aiohttp_cors
import aiohttp_jinja2
import aiomonitor
import aiotools
import click
import jinja2
import memray
import pyroscope
from aiohttp import web
from aiohttp.web_app import CleanupError
from setproctitle import setproctitle
from tenacity import AsyncRetrying, TryAgain, retry_if_exception_type, wait_exponential

from ai.backend.appproxy.common.config import get_default_redis_key_ttl
from ai.backend.appproxy.common.defs import (
    AGENTID_WORKER,
    APPPROXY_ANYCAST_STREAM_KEY,
    APPPROXY_BROADCAST_CHANNEL,
)
from ai.backend.appproxy.common.events import (
    AppProxyCircuitCreatedEvent,
    AppProxyCircuitRemovedEvent,
    AppProxyCircuitRouteUpdatedEvent,
    AppProxyWorkerCircuitAddedEvent,
)
from ai.backend.appproxy.common.exceptions import (
    BackendError,
    CoordinatorConnectionError,
    GenericBadRequest,
    GenericForbidden,
    InternalServerError,
    MethodNotAllowed,
    URLNotFound,
)
from ai.backend.appproxy.common.types import (
    AppCreator,
    FrontendMode,
    FrontendServerMode,
    ProxyProtocol,
    WebMiddleware,
    WebRequestHandler,
)
from ai.backend.appproxy.common.utils import (
    BackendAIAccessLogger,
    ensure_json_serializable,
    mime_match,
)
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.defs import (
    REDIS_LIVE_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
    RedisRole,
)
from ai.backend.common.events.dispatcher import EventDispatcher, EventHandler, EventProducer
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
from ai.backend.common.types import AgentId, RedisProfileTarget, ServiceDiscoveryType
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel
from ai.backend.logging.otel import OpenTelemetrySpec

from . import __version__
from .config import ServerConfig
from .config import load as load_config
from .coordinator_client import (
    deregister_worker,
    list_worker_circuits,
    ping_worker,
    register_worker,
)
from .metrics import collect_inference_metric
from .proxy.frontend import (
    H2PortFrontend,
    H2SubdomainFrontend,
    HTTPPortFrontend,
    HTTPSubdomainFrontend,
    TCPFrontend,
    TraefikPortFrontend,
    TraefikSubdomainFrontend,
    TraefikTCPFrontend,
)
from .types import Circuit, CleanupContext, RootContext, WorkerMetricRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

REDIS_APPPROXY_DB: Final[int] = 10  # FIXME: move to ai.backend.common.defs
EVENT_DISPATCHER_CONSUMER_GROUP: Final[str] = "appproxy-worker"

global_subapp_pkgs: Final[list[str]] = [
    ".health",
    ".setup",
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
    request_id = request.headers.get("X-BackendAI-RequestID", str(uuid.uuid4()))
    request["request_id"] = request_id
    if _current_task := asyncio.current_task():
        setattr(_current_task, "request_id", request_id)
    resp = await _handler(request)
    return resp


@web.middleware
async def exception_middleware(
    request: web.Request, handler: WebRequestHandler
) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]

    try:
        resp = await handler(request)
    except BackendError as ex:
        if ex.status_code == 500:
            log.exception("Internal server error raised inside handlers")
        if mime_match(request.headers.get("accept", "text/html"), "application/json", strict=True):
            return web.json_response(
                ensure_json_serializable(ex.body_dict),
                status=ex.status_code,
                headers={"Access-Control-Allow-Origin": "*"},
            )
        else:
            return aiohttp_jinja2.render_template(
                "error.jinja2",
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


async def request_counter_marker(root_ctx: RootContext) -> None:
    """Request counter marker function using the valkey client."""
    while True:
        try:
            redis_key = await root_ctx.request_counter_redis_queue.get()
            await root_ctx.valkey_live.incr_live_data(redis_key)
        except Exception:
            # log errors and keep going on
            log.exception("request_counter_marker(): error while handling request:")


async def last_used_time_marker(root_ctx: RootContext) -> None:
    """Last used time marker function using the valkey client."""
    while True:
        try:
            keys, last_used = await root_ctx.last_used_time_marker_redis_queue.get()
            data = {key: str(last_used) for key in keys}
            ttl = get_default_redis_key_ttl()
            await root_ctx.valkey_live.store_multiple_live_data(data, ex=ttl)
        except Exception:
            # log errors and keep going on
            log.exception("last_used_time_marker(): error while handling request:")


@actxmgr
async def redis_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    redis_profile_target = RedisProfileTarget.from_dict(root_ctx.local_config.redis.to_dict())

    root_ctx.valkey_live = await ValkeyLiveClient.create(
        valkey_target=redis_profile_target.profile_target(RedisRole.LIVE).to_valkey_target(),
        db_id=REDIS_LIVE_DB,
        human_readable_name="appproxy-worker",
    )
    root_ctx.valkey_stat = await ValkeyStatClient.create(
        valkey_target=redis_profile_target.profile_target(RedisRole.STATISTICS).to_valkey_target(),
        db_id=REDIS_STATISTICS_DB,
        human_readable_name="appproxy-worker",
    )
    root_ctx.last_used_time_marker_redis_queue = asyncio.Queue()
    root_ctx.request_counter_redis_queue = asyncio.Queue()

    last_used_time_marker_task = asyncio.create_task(last_used_time_marker(root_ctx))
    request_counter_marker_task = asyncio.create_task(request_counter_marker(root_ctx))

    yield

    last_used_time_marker_task.cancel()
    await last_used_time_marker_task
    request_counter_marker_task.cancel()
    await request_counter_marker_task

    await root_ctx.valkey_live.close()
    await root_ctx.valkey_stat.close()


@actxmgr
async def http_client_pool_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from functools import partial

    import aiohttp

    from ai.backend.common.clients.http_client.client_pool import (
        ClientPool,
        tcp_client_session_factory,
    )

    client_timeout = aiohttp.ClientTimeout(
        total=None,
        connect=10.0,
        sock_connect=10.0,
        sock_read=None,
    )
    cleanup_interval = root_ctx.local_config.proxy_worker.client_pool_cleanup_interval

    root_ctx.http_client_pool = ClientPool(
        partial(
            tcp_client_session_factory,
            timeout=client_timeout,
            ssl=True,  # SSL verification per endpoint via ClientKey
        ),
        cleanup_interval_seconds=cleanup_interval,
    )
    try:
        yield
    finally:
        await root_ctx.http_client_pool.close()


async def _make_message_queue(
    root_ctx: RootContext,
) -> AbstractMessageQueue:
    node_id = root_ctx.local_config.proxy_worker.id
    redis_profile_target = RedisProfileTarget.from_dict(root_ctx.local_config.redis.to_dict())

    stream_redis_target = redis_profile_target.profile_target(RedisRole.STREAM)

    args = RedisMQArgs(
        anycast_stream_key=APPPROXY_ANYCAST_STREAM_KEY,
        broadcast_channel=APPPROXY_BROADCAST_CHANNEL,
        consume_stream_keys={
            APPPROXY_ANYCAST_STREAM_KEY,
        },
        subscribe_channels={
            APPPROXY_BROADCAST_CHANNEL,
        },
        group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
        node_id=node_id,
        db=REDIS_STREAM_DB,
    )

    if root_ctx.local_config.proxy_worker.use_experimental_redis_event_dispatcher:
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
    mq = await _make_message_queue(root_ctx)
    root_ctx.event_producer = EventProducer(
        mq,
        source=AGENTID_WORKER,
        log_events=root_ctx.local_config.debug.log_events,
    )
    root_ctx.event_dispatcher = EventDispatcher(
        mq,
        log_events=root_ctx.local_config.debug.log_events,
        event_observer=root_ctx.metrics.event,
    )
    await root_ctx.event_dispatcher.start()

    yield

    await root_ctx.event_producer.close()
    await asyncio.sleep(0.2)
    await root_ctx.event_dispatcher.close()


@actxmgr
async def event_handler_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    handlers: list[EventHandler] = [
        root_ctx.event_dispatcher.subscribe(
            evt, root_ctx, handle_proxy_route_event, name="proxy-worker"
        )
        for evt in (
            AppProxyCircuitCreatedEvent,
            AppProxyCircuitRouteUpdatedEvent,
            AppProxyCircuitRemovedEvent,
        )
    ]
    yield
    for handler in handlers:
        root_ctx.event_dispatcher.unsubscribe(handler)


@actxmgr
async def proxy_frontend_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    match (
        root_ctx.local_config.proxy_worker.protocol,
        root_ctx.local_config.proxy_worker.frontend_mode,
    ):
        case (ProxyProtocol.HTTP, FrontendServerMode.TRAEFIK):
            assert root_ctx.local_config.proxy_worker.traefik
            match root_ctx.local_config.proxy_worker.traefik.frontend_mode:
                case FrontendMode.PORT:
                    root_ctx.proxy_frontend = TraefikPortFrontend(root_ctx)
                case FrontendMode.WILDCARD_DOMAIN:
                    root_ctx.proxy_frontend = TraefikSubdomainFrontend(root_ctx)
        case (ProxyProtocol.TCP, FrontendServerMode.TRAEFIK):
            assert (
                root_ctx.local_config.proxy_worker.traefik
                and root_ctx.local_config.proxy_worker.traefik.port_proxy
            )
            root_ctx.proxy_frontend = TraefikTCPFrontend(root_ctx)
        case (ProxyProtocol.HTTP, FrontendServerMode.PORT):
            root_ctx.proxy_frontend = HTTPPortFrontend(root_ctx)
        case (ProxyProtocol.HTTP, FrontendServerMode.WILDCARD_DOMAIN):
            root_ctx.proxy_frontend = HTTPSubdomainFrontend(root_ctx)
        case (ProxyProtocol.TCP, FrontendServerMode.PORT):
            root_ctx.proxy_frontend = TCPFrontend(root_ctx)
        case (ProxyProtocol.HTTP2, FrontendServerMode.PORT):
            root_ctx.proxy_frontend = H2PortFrontend(root_ctx)
        case (ProxyProtocol.HTTP2, FrontendServerMode.WILDCARD_DOMAIN):
            root_ctx.proxy_frontend = H2SubdomainFrontend(root_ctx)
        case _:
            log.error("Unsupported protocol {}", root_ctx.local_config.proxy_worker.protocol)
    await root_ctx.proxy_frontend.start()
    log.debug("started proxy protocol {}", root_ctx.proxy_frontend.__class__.__name__)
    yield
    await root_ctx.proxy_frontend.terminate_all_circuits()
    try:
        await root_ctx.proxy_frontend.stop()
    except CleanupError as ee:
        if all([isinstance(e, asyncio.CancelledError) for e in ee.exceptions]):
            raise asyncio.CancelledError()
        else:
            raise ee


@actxmgr
async def worker_registration_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    async for attempt in AsyncRetrying(
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(TryAgain),
    ):
        with attempt:
            try:
                await register_worker(root_ctx, str(uuid.uuid4()))
            except CoordinatorConnectionError:
                log.warning(
                    "Failed to connect to coordinator {}, retrying...",
                    root_ctx.local_config.proxy_worker.coordinator_endpoint,
                )
                raise TryAgain

    circuits = await list_worker_circuits(root_ctx, str(uuid.uuid4()))
    for circuit in circuits:
        await root_ctx.proxy_frontend.register_circuit(circuit, circuit.route_info)

    async def _heartbeat(interval: float):
        try:
            async for attempt in AsyncRetrying(
                wait=wait_exponential(multiplier=1, min=4, max=10),
                retry=retry_if_exception_type(TryAgain),
            ):
                with attempt:
                    try:
                        await ping_worker(root_ctx, str(uuid.uuid4()))
                    except CoordinatorConnectionError:
                        log.warning(
                            "Failed to ping coordinator {}, retrying...",
                            root_ctx.local_config.proxy_worker.coordinator_endpoint,
                        )

        except Exception as e:
            log.warning("Failed to ping coordinator: {}", str(e))

    timer = aiotools.create_timer(_heartbeat, root_ctx.local_config.proxy_worker.heartbeat_period)
    yield
    timer.cancel()
    await timer
    await deregister_worker(root_ctx, str(uuid.uuid4()))


@actxmgr
async def inference_metric_collection_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    timer = aiotools.create_timer(
        functools.partial(collect_inference_metric, root_ctx),
        root_ctx.local_config.proxy_worker.inference_metric_collection_interval,
    )
    yield
    timer.cancel()
    await timer


@actxmgr
async def service_discovery_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    sd_type = root_ctx.local_config.service_discovery.type
    service_discovery: ServiceDiscovery
    match sd_type:
        case ServiceDiscoveryType.REDIS:
            redis_profile_target = RedisProfileTarget.from_dict(
                root_ctx.local_config.redis.to_dict()
            )
            live_redis_target = redis_profile_target.profile_target(RedisRole.LIVE)
            service_discovery = await RedisServiceDiscovery.create(
                RedisServiceDiscoveryArgs(valkey_target=live_redis_target.to_valkey_target())
            )
        case _:
            raise RuntimeError(f"Unsupported service discovery type: {sd_type}")

    # Determine announce addresses
    announce_addr = root_ctx.local_config.proxy_worker.announce_addr
    assert announce_addr is not None  # auto-populated if None
    sd_loop = ServiceDiscoveryLoop(
        sd_type,
        service_discovery,
        ServiceMetadata(
            display_name=f"appproxy-worker-{root_ctx.local_config.proxy_worker.authority}",
            service_group="appproxy-worker",
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


async def metrics(request: web.Request) -> web.Response:
    request["do_not_print_access_log"] = True
    root_ctx: RootContext = request.app["_root.context"]
    allowed_network = ipaddress.IPv4Network(
        root_ctx.local_config.proxy_worker.metric_access_allowed_hosts
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


async def hello(request: web.Request) -> web.Response:
    """
    Returns the API version number.
    """
    return web.json_response({
        "proxy-worker": __version__,
    })


async def status(request: web.Request) -> web.Response:
    request["do_not_print_access_log"] = True
    return web.json_response({"api_version": "v2"})


async def handle_proxy_route_event(
    context: RootContext,
    agent_id: AgentId,
    event: AppProxyCircuitCreatedEvent
    | AppProxyCircuitRouteUpdatedEvent
    | AppProxyCircuitRemovedEvent,
) -> None:
    if event.target_worker_authority != context.local_config.proxy_worker.authority:
        return

    match event:
        case AppProxyCircuitCreatedEvent():
            log.debug(
                "handle_proxy_route_event(evt: AppProxyCircuitCreatedEvent({}))",
                [c.id for c in event.circuits],
            )
            for circuit in event.circuits:
                await context.proxy_frontend.register_circuit(
                    Circuit.from_serialized_circuit(circuit), circuit.route_info
                )
            await context.event_producer.broadcast_event(
                AppProxyWorkerCircuitAddedEvent(
                    target_worker_authority=context.local_config.proxy_worker.authority,
                    circuits=event.circuits,
                )
            )
        case AppProxyCircuitRouteUpdatedEvent():
            log.debug(
                "handle_proxy_route_event(evt: AppProxyCircuitRouteUpdatedEvent({}))",
                event.circuit.id,
            )
            await context.proxy_frontend.update_circuit_route_info(
                Circuit.from_serialized_circuit(event.circuit), event.routes
            )
        case AppProxyCircuitRemovedEvent():
            log.debug(
                "handle_proxy_route_event(evt: AppProxyCircuitRemovedEvent({}))",
                [c.id for c in event.circuits],
            )
            for circuit in event.circuits:
                await context.proxy_frontend.break_circuit(Circuit.from_serialized_circuit(circuit))


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
    root_app.middlewares.extend(global_middlewares)  # type: ignore


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
    root_ctx = RootContext()
    root_ctx.metrics = WorkerMetricRegistry.instance()

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
        if local_config.proxy_worker.frontend_mode == FrontendServerMode.TRAEFIK:
            # traefik won't require event dispatcher
            cleanup_contexts = [
                proxy_frontend_ctx,
                redis_ctx,
                http_client_pool_ctx,
                service_discovery_ctx,
                worker_registration_ctx,
                inference_metric_collection_ctx,
            ]
        else:
            cleanup_contexts = [
                proxy_frontend_ctx,
                redis_ctx,
                http_client_pool_ctx,
                event_dispatcher_ctx,
                event_handler_ctx,
                service_discovery_ctx,
                worker_registration_ctx,
                inference_metric_collection_ctx,
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
    cors.add(app.router.add_route("GET", "/metrics", metrics))
    if subapp_pkgs is None:
        subapp_pkgs = []
    for pkg_name in subapp_pkgs:
        if pidx == 0:
            log.info("Loading module: {0}", pkg_name[1:])
        subapp_mod = importlib.import_module(pkg_name, "ai.backend.appproxy.worker.api")
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
        host="0.0.0.0",
        termui_port=root_ctx.local_config.proxy_worker.aiomonitor_termui_port + pidx,
        webui_port=root_ctx.local_config.proxy_worker.aiomonitor_webui_port + pidx,
        console_enabled=False,
        hook_task_factory=root_ctx.local_config.debug.enhanced_aiomonitor_task_info,
    )
    m.prompt = f"monitor (proxy-worker[{pidx}@{os.getpid()}]) >>> "
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
        if root_ctx.local_config.proxy_worker.tls_listen:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(
                str(root_ctx.local_config.proxy_worker.tls_cert),
                str(root_ctx.local_config.proxy_worker.tls_privkey),
            )

        runner = web.AppRunner(
            root_app, keepalive_timeout=30.0, access_log_class=BackendAIAccessLogger
        )
        await runner.setup()
        service_addr = root_ctx.local_config.proxy_worker.api_bind_addr
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
            uid = root_ctx.local_config.proxy_worker.user
            gid = root_ctx.local_config.proxy_worker.group
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
            await runner.cleanup()
    finally:
        if aiomon_started:
            m.close()
        log.debug("The number of leftover asyncio tasks: {}", len(asyncio.all_tasks()))


@actxmgr
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: tuple[ServerConfig, str],
) -> AsyncIterator[None]:
    setproctitle(f"backend.ai: proxy-worker worker-{pidx}")
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
        traceback.print_exc()


@click.group(invoke_without_command=True)
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=Path,
    default=None,
    help=(
        "The config file path. (default: ./proxy-worker.toml and /etc/backend.ai/proxy-worker.toml)"
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
    Start the proxy-worker service as a foreground process.
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
        server_config.proxy_worker.pid_file.touch(exist_ok=True)
        server_config.proxy_worker.pid_file.write_text(str(os.getpid()))
        ipc_base_path = server_config.proxy_worker.ipc_base_path
        ipc_base_path.mkdir(exist_ok=True, parents=True)
        log_sockpath = ipc_base_path / f"worker-logger-{os.getpid()}.sock"
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
                setproctitle("backend.ai: proxy-worker")
                log.info("Backend.AI AppProxy Worker {0}", __version__)
                log.info("runtime: {0}", env_info())
                if server_config.profiling.enable_pyroscope:
                    log.info("Pyroscope tracing enabled")
                if server_config.profiling.enable_memray:
                    log.info("Memray tracing enabled")
                log_config = logging.getLogger("ai.backend.appproxy.worker.config")
                log_config.debug("debug mode enabled.")
                if server_config.proxy_worker.event_loop == "uvloop":
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
            if server_config.proxy_worker.pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                server_config.proxy_worker.pid_file.unlink()
            if tracker:
                tracker.__exit__(None, None, None)
    else:
        # Click is going to invoke a subcommand.
        pass


if __name__ == "__main__":
    sys.exit(main())
