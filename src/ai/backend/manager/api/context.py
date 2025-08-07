from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
    from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
    from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
    from ai.backend.common.events.fetcher import EventFetcher
    from ai.backend.common.events.hub.hub import EventHub
    from ai.backend.common.message_queue.queue import AbstractMessageQueue
    from ai.backend.common.metrics.metric import CommonMetricRegistry
    from ai.backend.common.plugin.event import EventDispatcherPluginContext
    from ai.backend.common.plugin.hook import HookPluginContext
    from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
    from ai.backend.common.service_discovery.service_discovery import (
        ServiceDiscovery,
        ServiceDiscoveryLoop,
    )
    from ai.backend.common.types import ValkeyProfileTarget
    from ai.backend.manager.sokovan.sokovan import SokovanOrchestrator

    from ..agent_cache import AgentRPCCache
    from ..config.provider import ManagerConfigProvider
    from ..idle import IdleCheckerHost
    from ..models.storage import StorageSessionManager
    from ..models.utils import ExtendedAsyncSAEngine
    from ..plugin.network import NetworkPluginContext
    from ..plugin.webapp import WebappPluginContext
    from ..registry import AgentRegistry
    from ..repositories.repositories import Repositories
    from ..scheduler.dispatcher import SchedulerDispatcher
    from ..service.base import ServicesContext
    from ..services.processors import Processors
    from ..types import DistributedLockFactory
    from .types import CORSOptions


class BaseContext:
    pass


@attrs.define(slots=True, auto_attribs=True, init=False)
class RootContext(BaseContext):
    pidx: int
    db: ExtendedAsyncSAEngine
    distributed_lock_factory: DistributedLockFactory
    event_dispatcher: EventDispatcher
    event_fetcher: EventFetcher
    event_producer: EventProducer
    etcd: AsyncEtcd
    valkey_live: ValkeyLiveClient
    valkey_stat: ValkeyStatClient
    valkey_image: ValkeyImageClient
    valkey_stream: ValkeyStreamClient
    valkey_profile_target: ValkeyProfileTarget
    config_provider: ManagerConfigProvider
    cors_options: CORSOptions

    webapp_plugin_ctx: WebappPluginContext
    idle_checker_host: IdleCheckerHost
    storage_manager: StorageSessionManager
    hook_plugin_ctx: HookPluginContext
    network_plugin_ctx: NetworkPluginContext
    event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    services_ctx: ServicesContext

    registry: AgentRegistry
    agent_cache: AgentRPCCache
    scheduler_dispatcher: SchedulerDispatcher
    sokovan_orchestrator: SokovanOrchestrator

    error_monitor: ErrorPluginContext
    stats_monitor: StatsPluginContext
    background_task_manager: BackgroundTaskManager
    metrics: CommonMetricRegistry
    repositories: Repositories
    processors: Processors
    event_hub: EventHub
    message_queue: AbstractMessageQueue
    service_discovery: ServiceDiscovery
    sd_loop: ServiceDiscoveryLoop
