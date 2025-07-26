import asyncio
from dataclasses import dataclass
from typing import override

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.common.types import AGENTID_MANAGER
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.setup.provisioners.message_queue import MessageQueueStage


@dataclass
class EventProducerResult:
    event_fetcher: EventFetcher
    event_producer: EventProducer


@dataclass
class EventProducerSpec:
    message_queue: AbstractMessageQueue
    log_events: bool


class EventProducerProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "event-producer-provisioner"

    @override
    async def setup(self, spec: EventProducerSpec) -> EventProducerResult:
        event_fetcher = EventFetcher(spec.message_queue)
        event_producer = EventProducer(
            spec.message_queue,
            source=AGENTID_MANAGER,
            log_events=spec.log_events,
        )
        return EventProducerResult(
            event_fetcher=event_fetcher,
            event_producer=event_producer,
        )

    @override
    async def teardown(self, resource: EventProducerResult) -> None:
        await resource.event_producer.close()
        await asyncio.sleep(0.2)


class EventProducerSpecGenerator(SpecGenerator[EventProducerSpec]):
    def __init__(self, message_queue_stage: MessageQueueStage, config: ManagerUnifiedConfig):
        self.message_queue_stage = message_queue_stage
        self.config = config

    @override
    async def wait_for_spec(self) -> EventProducerSpec:
        message_queue = await self.message_queue_stage.wait_for_resource()
        return EventProducerSpec(
            message_queue=message_queue, log_events=self.config.debug.log_events
        )


# Type alias for EventProducer stage
EventProducerStage = ProvisionStage[EventProducerSpec, EventProducerResult]
