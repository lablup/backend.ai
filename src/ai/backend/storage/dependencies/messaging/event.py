from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.types import AGENTID_STORAGE


@dataclass
class EventProducerInput:
    """Input required for the event producer setup."""

    message_queue: AbstractMessageQueue
    log_events: bool


@dataclass
class EventDispatcherInput:
    """Input required for the event dispatcher setup."""

    message_queue: AbstractMessageQueue
    log_events: bool
    metric_registry: CommonMetricRegistry


class EventProducerProvider(NonMonitorableDependencyProvider[EventProducerInput, EventProducer]):
    """Provider for the event producer."""

    @property
    @override
    def stage_name(self) -> str:
        return "event-producer"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: EventProducerInput) -> AsyncIterator[EventProducer]:
        producer = EventProducer(
            setup_input.message_queue,
            source=AGENTID_STORAGE,
            log_events=setup_input.log_events,
        )
        try:
            yield producer
        finally:
            await producer.close()


class EventDispatcherProvider(
    NonMonitorableDependencyProvider[EventDispatcherInput, EventDispatcher]
):
    """Provider for the event dispatcher."""

    @property
    @override
    def stage_name(self) -> str:
        return "event-dispatcher"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: EventDispatcherInput) -> AsyncIterator[EventDispatcher]:
        dispatcher = EventDispatcher(
            setup_input.message_queue,
            log_events=setup_input.log_events,
            event_observer=setup_input.metric_registry.event,
        )
        await dispatcher.start()
        try:
            yield dispatcher
        finally:
            await dispatcher.close()
