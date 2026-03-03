from __future__ import annotations

import dataclasses
from collections.abc import Awaitable, Callable, Iterable, Mapping
from typing import TYPE_CHECKING

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware

from ai.backend.common.api_handlers import APIResponse, APIStreamResponse

if TYPE_CHECKING:
    from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
    from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
    from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
    from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
        ValkeyRateLimitClient,
    )
    from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.common.metrics.metric import GraphQLMetricObserver
    from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.idle import IdleCheckerHost
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
    from ai.backend.manager.plugin.network import NetworkPluginContext
    from ai.backend.manager.registry import AgentRegistry
    from ai.backend.manager.repositories.agent.repository import AgentRepository
    from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
    from ai.backend.manager.repositories.user.repository import UserRepository
    from ai.backend.manager.service.base import ServicesContext
    from ai.backend.manager.services.processors import Processors

    from .routing import RouteRegistry

type WebRequestHandler = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
type WebMiddleware = Middleware

type CORSOptions = Mapping[str, aiohttp_cors.ResourceOptions]
type AppCreator = Callable[
    [CORSOptions],
    tuple[web.Application, Iterable[WebMiddleware]],
]

type RouteMiddleware = Callable[
    [WebRequestHandler],
    WebRequestHandler,
]

type ApiHandler = Callable[..., Awaitable[APIResponse | APIStreamResponse | web.StreamResponse]]


@dataclasses.dataclass(frozen=True, slots=True)
class GQLContextDeps:
    """Dependencies needed to construct ``GraphQueryContext`` for GraphQL execution.

    Injected into ``AdminHandler`` at startup so that the handler does not
    access ``RootContext`` at request time.  Temporary scaffolding that will
    be removed when Phase 2 (full DI) lands.
    """

    config_provider: ManagerConfigProvider
    etcd: AsyncEtcd
    db: ExtendedAsyncSAEngine
    valkey_stat: ValkeyStatClient
    valkey_image: ValkeyImageClient
    valkey_live: ValkeyLiveClient
    valkey_schedule: ValkeyScheduleClient
    network_plugin_ctx: NetworkPluginContext
    background_task_manager: BackgroundTaskManager
    services_ctx: ServicesContext
    storage_manager: StorageSessionManager
    registry: AgentRegistry
    idle_checker_host: IdleCheckerHost
    metric_observer: GraphQLMetricObserver
    processors: Processors
    scheduler_repository: SchedulerRepository
    user_repository: UserRepository
    agent_repository: AgentRepository


@dataclasses.dataclass(frozen=True, slots=True)
class ModuleDeps:
    """Shared dependencies injected into all API module registrar functions."""

    cors_options: CORSOptions
    processors: Processors
    config_provider: ManagerConfigProvider
    gql_context_deps: GQLContextDeps | None = None
    valkey_rate_limit: ValkeyRateLimitClient | None = None


type ModuleRegistrar = Callable[[ModuleDeps], RouteRegistry]
