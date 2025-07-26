import asyncio
from dataclasses import dataclass
from typing import override

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.stage.types import Provisioner
from ai.backend.common.types import AGENTID_MANAGER


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
