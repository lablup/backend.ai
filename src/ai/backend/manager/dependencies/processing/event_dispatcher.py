from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventDispatcher, EventObserver
from ai.backend.common.message_queue.abc.queue import AbstractMessageQueue


@dataclass
class EventDispatcherInput:
    """Input required for EventDispatcher setup."""

    message_queue: AbstractMessageQueue
    log_events: bool
    event_observer: EventObserver | None


class EventDispatcherDependency(
    NonMonitorableDependencyProvider[EventDispatcherInput, EventDispatcher]
):
    """Provides EventDispatcher lifecycle management.

    Creates the EventDispatcher instance. Note that start() and handler
    registration are done in ProcessingComposer after all dependencies are ready.
    """

    @property
    def stage_name(self) -> str:
        return "event-dispatcher"

    @asynccontextmanager
    async def provide(self, setup_input: EventDispatcherInput) -> AsyncIterator[EventDispatcher]:
        dispatcher = EventDispatcher(
            setup_input.message_queue,
            log_events=setup_input.log_events,
            event_observer=setup_input.event_observer,
        )
        try:
            yield dispatcher
        finally:
            await dispatcher.close()
