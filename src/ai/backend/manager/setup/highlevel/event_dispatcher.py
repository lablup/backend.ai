from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.metrics.metric import EventMetricObserver
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.event_dispatcher.dispatch import DispatcherArgs, Dispatchers
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.setup.core.agent_registry import AgentRegistryResource
from ai.backend.manager.setup.infrastructure.redis import ValkeyClients


@dataclass
class EventDispatcherSpec:
    config: ManagerUnifiedConfig
    message_queue: AbstractMessageQueue
    valkey_clients: ValkeyClients
    scheduler_dispatcher: SchedulerDispatcher
    event_hub: EventHub
    agent_registry_resource: AgentRegistryResource
    database: ExtendedAsyncSAEngine
    idle_checker_host: IdleCheckerHost
    event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    event_observer: EventMetricObserver


class EventDispatcherProvisioner(Provisioner[EventDispatcherSpec, EventDispatcher]):
    @property
    def name(self) -> str:
        return "event_dispatcher"

    async def setup(self, spec: EventDispatcherSpec) -> EventDispatcher:
        # Create the event dispatcher with monitoring
        event_dispatcher = EventDispatcher(
            spec.message_queue,
            log_events=spec.config.debug.log_events,
            event_observer=spec.event_observer,
        )
        
        # Create and configure dispatchers
        dispatchers = Dispatchers(
            DispatcherArgs(
                spec.valkey_clients.valkey_stream,
                spec.scheduler_dispatcher,
                spec.event_hub,
                spec.agent_registry_resource.registry,
                spec.database,
                spec.idle_checker_host,
                spec.event_dispatcher_plugin_ctx,
            )
        )
        dispatchers.dispatch(event_dispatcher)
        
        # Start the event dispatcher
        await event_dispatcher.start()
        
        return event_dispatcher

    async def teardown(self, resource: EventDispatcher) -> None:
        await resource.close()