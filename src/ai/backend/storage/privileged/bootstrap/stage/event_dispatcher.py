from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.metrics.metric import EventMetricObserver
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import AgentId

SOURCE_ID = AgentId("storage-proxy-privileged")


@dataclass
class EventDispatcherSpec:
    message_queue: AbstractMessageQueue
    log_events: bool
    event_observer: EventMetricObserver
    source_id: Optional[AgentId]


@dataclass
class EventDispatcherResult:
    event_producer: EventProducer
    event_dispatcher: EventDispatcher


class EventDispatcherSpecGenerator(ArgsSpecGenerator[EventDispatcherSpec]):
    pass


class EventDispatcherProvisioner(Provisioner[EventDispatcherSpec, EventDispatcherResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-event-dispatcher"

    @override
    async def setup(self, spec: EventDispatcherSpec) -> EventDispatcherResult:
        source_id = spec.source_id or SOURCE_ID
        event_producer = EventProducer(
            spec.message_queue,
            source=source_id,
            log_events=spec.log_events,
        )
        event_dispatcher = EventDispatcher(
            spec.message_queue,
            log_events=spec.log_events,
            event_observer=spec.event_observer,
        )
        return EventDispatcherResult(event_producer, event_dispatcher)

    @override
    async def teardown(self, resource: EventDispatcherResult) -> None:
        await resource.event_producer.close()
        await resource.event_dispatcher.close()


class EventDispatcherStage(ProvisionStage[EventDispatcherSpec, EventDispatcherResult]):
    pass
