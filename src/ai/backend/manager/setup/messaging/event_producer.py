from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.stage.types import Provisioner
from ai.backend.common.types import AGENTID_MANAGER
from ai.backend.manager.config.unified import ManagerUnifiedConfig


@dataclass
class EventProducerSpec:
    config: ManagerUnifiedConfig
    message_queue: AbstractMessageQueue


@dataclass
class EventProducerResource:
    event_producer: EventProducer
    event_fetcher: EventFetcher


class EventProducerProvisioner(Provisioner[EventProducerSpec, EventProducerResource]):
    @property
    def name(self) -> str:
        return "event_producer"

    async def setup(self, spec: EventProducerSpec) -> EventProducerResource:
        event_fetcher = EventFetcher(spec.message_queue)
        event_producer = EventProducer(
            spec.message_queue,
            source=AGENTID_MANAGER,
            log_events=spec.config.debug.log_events,
        )
        return EventProducerResource(
            event_producer=event_producer,
            event_fetcher=event_fetcher,
        )

    async def teardown(self, resource: EventProducerResource) -> None:
        await resource.event_producer.close()
        # event_fetcher doesn't have a close method