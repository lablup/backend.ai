from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.types import AGENTID_MANAGER
from ai.backend.manager.config.unified import ManagerUnifiedConfig


@dataclass
class EventProducerInput:
    """Input required for event producer setup.

    Contains the message queue and configuration.
    """

    message_queue: AbstractMessageQueue
    config: ManagerUnifiedConfig


class EventProducerDependency(NonMonitorableDependencyProvider[EventProducerInput, EventProducer]):
    """Provides EventProducer lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "event-producer"

    @asynccontextmanager
    async def provide(self, setup_input: EventProducerInput) -> AsyncIterator[EventProducer]:
        """Initialize and provide the event producer.

        Args:
            setup_input: Input containing message queue and configuration

        Yields:
            Initialized EventProducer
        """
        event_producer = EventProducer(
            setup_input.message_queue,
            source=AGENTID_MANAGER,
            log_events=setup_input.config.debug.log_events,
        )
        try:
            yield event_producer
        finally:
            await event_producer.close()
            await asyncio.sleep(0.2)
