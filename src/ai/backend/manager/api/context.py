from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscovery,
    ServiceDiscoveryLoop,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.service.base import ServicesContext
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
    from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
    from ai.backend.common.plugin.hook import HookPluginContext
    from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
    from ai.backend.common.types import RedisConnectionInfo

    from ..agent_cache import AgentRPCCache
    from ..idle import IdleCheckerHost
    from ..models.storage import StorageSessionManager
    from ..models.utils import ExtendedAsyncSAEngine
    from ..plugin.webapp import WebappPluginContext
    from ..registry import AgentRegistry
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
    event_producer: EventProducer
    etcd: AsyncEtcd
    redis_live: RedisConnectionInfo
    redis_stat: RedisConnectionInfo
    redis_image: RedisConnectionInfo
    redis_stream: RedisConnectionInfo
    redis_lock: RedisConnectionInfo
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

    error_monitor: ErrorPluginContext
    stats_monitor: StatsPluginContext
    background_task_manager: BackgroundTaskManager
    metrics: CommonMetricRegistry
    processors: Processors
    event_hub: EventHub
    message_queue: AbstractMessageQueue
    service_discovery: ServiceDiscovery
    sd_loop: ServiceDiscoveryLoop

    def __init__(self, *, metrics: CommonMetricRegistry = CommonMetricRegistry(), **kwargs) -> None:
        super().__init__(**kwargs)
        self.metrics = metrics
