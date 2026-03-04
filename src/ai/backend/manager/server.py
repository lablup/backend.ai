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
    TYPE_CHECKING,
    Any,
    Final,
)

import aiohttp_cors
import aiomonitor
import aiotools
import click
import uvloop
from aiohttp import web
from aiohttp.typedefs import Handler, Middleware
from aiotools import apartial
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
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
from ai.backend.common.types import (
    AgentSelectionStrategy,
)
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel
from ai.backend.logging.otel import (
    instrument_aiohttp_client,
    instrument_aiohttp_server,
)

from . import __version__
from .api import ManagerStatus
from .api.rest import build_api_routes
from .api.rest.middleware import (
    build_api_metric_middleware,
    build_auth_middleware,
    build_exception_middleware,
    request_id_middleware,
)
from .api.rest.ratelimit.handler import rlim_middleware
from .api.rest.routing import RouteRegistry
from .api.rest.types import GQLContextDeps, ModuleDeps, ModuleRegistrar
from .config.bootstrap import BootstrapConfig
from .config.unified import EventLoopType
from .dependencies import DependencyInput, DependencyResources, ManagerDependencyComposer
from .dependencies.errors import DependencyInitializationError
from .errors.common import (
    GenericBadRequest,
    InternalServerError,
    ServerMisconfiguredError,
)
from .plugin.webapp import WebappPluginContext

if TYPE_CHECKING:
    from .api.rest.types import WebRequestHandler

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

EVENT_DISPATCHER_CONSUMER_GROUP: Final = "manager"


async def hello(_request: web.Request) -> web.Response:
    """
    Returns the API version number.
    """
    return web.json_response({
        "version": LATEST_API_VERSION,
        "manager": __version__,
    })


async def on_prepare(_request: web.Request, response: web.StreamResponse) -> None:
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
        request._match_info = new_match_info
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
    return await _handler(request)


# exception_middleware and auth_middleware are now created via factory functions
# (build_exception_middleware / build_auth_middleware) in the middleware package.
# They are inserted into the root application middleware list in server_main()
# after all dependencies are initialized.


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


def _mount_registry_tree(
    root_app: web.Application,
    root_registry: RouteRegistry,
    pidx: int = 0,
) -> None:
    """Flatten the registry tree and mount all subapps on *root_app*."""

    async def _bridge_root_app(subapp: web.Application) -> None:
        subapp["_root_app"] = root_app

    for prefix, app, _reg in root_registry.collect_apps():
        if pidx == 0:
            log.info("Loading module: {}", prefix)
        app["_registry_prefix"] = prefix
        app.on_startup.insert(0, _bridge_root_app)
        root_app.add_subapp("/" + prefix, app)


def _setup_api(
    root_app: web.Application,
    dep_resources: DependencyResources,
    pidx: int,
) -> None:
    """Build the full API module tree and mount it on *root_app*.

    Must be called **after** the Composer has run (so that
    ``dep_resources.processing.processors`` is available) but **before**
    ``runner.setup()`` freezes the application router.
    """
    r = dep_resources
    gql_context_deps = GQLContextDeps(
        config_provider=r.bootstrap.config_provider,
        etcd=r.bootstrap.etcd,
        db=r.infrastructure.db,
        valkey_stat=r.infrastructure.valkey.stat,
        valkey_image=r.infrastructure.valkey.image,
        valkey_live=r.infrastructure.valkey.live,
        valkey_schedule=r.infrastructure.valkey.schedule,
        network_plugin_ctx=r.plugins.network_plugin_ctx,
        background_task_manager=r.system.background_task_manager,
        services_ctx=r.domain.services_ctx,
        storage_manager=r.components.storage_manager,
        registry=r.agents.registry,
        idle_checker_host=r.orchestration.idle_checker_host,
        metric_observer=r.system.metrics.gql,
        processors=r.processing.processors,
        scheduler_repository=r.domain.repositories.scheduler.repository,
        user_repository=r.domain.repositories.user.repository,
        agent_repository=r.domain.repositories.agent.repository,
    )
    deps = ModuleDeps(
        cors_options=r.system.cors_options,
        processors=r.processing.processors,
        config_provider=r.bootstrap.config_provider,
        pidx=pidx,
        storage_manager=r.components.storage_manager,
        export_repository=r.domain.repositories.export.repository,
        export_config=r.bootstrap.config_provider.config.export,
        gql_context_deps=gql_context_deps,
        valkey_rate_limit=r.infrastructure.valkey.rate_limit,
        event_hub=r.messaging.event_hub,
        event_fetcher=r.messaging.event_fetcher,
        stream_cleanup_handler=r.processing.stream_cleanup_handler,
        events_service=r.processing.events_service,
        stream_service=r.processing.stream_service,
        health_probe=r.system.health_probe,
        db=r.infrastructure.db,
        registry=r.agents.registry,
        error_monitor=r.monitoring.error_monitor,
        valkey_live=r.infrastructure.valkey.live,
        idle_checker_host=r.orchestration.idle_checker_host,
        etcd=r.bootstrap.etcd,
        event_dispatcher=r.processing.event_dispatcher,
    )

    # 1. Build API module tree
    root_registry = RouteRegistry.create("", deps.cors_options)
    for sub in build_api_routes(deps):
        root_registry.add_subregistry(sub)

    # 2. Flatten and mount all on root_app
    _mount_registry_tree(root_app, root_registry, pidx)

    # 3. Root middleware — only registered here, never from modules
    rlim_reg = root_registry.find_subregistry("ratelimit")
    if rlim_reg is not None and rlim_reg.ratelimit_ctx is not None:
        root_app.middlewares.append(web.middleware(apartial(rlim_middleware, rlim_reg.app)))


def register_modules(
    root_app: web.Application,
    registrars: Sequence[ModuleRegistrar],
    *,
    deps: ModuleDeps,
) -> None:
    """Register selected modules for test fixtures.

    Public API used by ``tests/component/conftest.py`` to register only
    the modules needed for a particular test.
    """
    root_registry = RouteRegistry.create("", deps.cors_options)
    for registrar in registrars:
        sub = registrar(deps)
        root_registry.add_subregistry(sub)
    _mount_registry_tree(root_app, root_registry)

    # Install ratelimit middleware on root app if the module is present
    rlim_reg = root_registry.find_subregistry("ratelimit")
    if rlim_reg is not None and rlim_reg.ratelimit_ctx is not None:
        root_app.middlewares.append(web.middleware(apartial(rlim_middleware, rlim_reg.app)))


def build_root_app(
    pidx: int,
    bootstrap_config: BootstrapConfig,
    *,
    scheduler_opts: Mapping[str, Any] | None = None,
) -> web.Application:
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

    metrics = CommonMetricRegistry.instance()
    cors_options = {
        "*": aiohttp_cors.ResourceOptions(  # type: ignore[no-untyped-call]
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }
    app = web.Application(
        middlewares=[
            request_id_middleware,
            # exception_middleware and auth_middleware are inserted later
            # in server_main() after dependencies are available.
            api_middleware,
            build_api_metric_middleware(metrics.api),
        ]
    )
    global_exception_handler = functools.partial(handle_loop_error)
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(global_exception_handler)

    # If the request path starts with the following route, the auth_middleware is bypassed.
    # In this case, all authentication flags are turned off.
    # Used in special cases where the request headers cannot be modified.
    app["auth_middleware_allowlist"] = [
        "/container-registries/webhook",
    ]

    app["_pidx"] = pidx
    app["_cors_options"] = cors_options
    app["_metrics"] = metrics
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

    cors = aiohttp_cors.setup(app, defaults=cors_options)
    # should be done in create_app() in other modules.
    cors.add(app.router.add_route("GET", r"", hello))
    cors.add(app.router.add_route("GET", r"/", hello))

    vendor_path = importlib.resources.files("ai.backend.manager.vendor")
    if not isinstance(vendor_path, Path):
        raise ServerMisconfiguredError("vendor_path must be a Path instance")
    app.router.add_static("/static/vendor", path=vendor_path, name="static")
    return app


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
        root_app = build_root_app(pidx, boostrap_config)

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
        if dep_resources.monitoring.error_monitor is None:
            raise DependencyInitializationError("error_monitor plugin failed to initialize")
        if dep_resources.monitoring.stats_monitor is None:
            raise DependencyInitializationError("stats_monitor plugin failed to initialize")
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
        _setup_api(root_app, dep_resources, pidx)

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
