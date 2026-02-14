from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.message_queue.queue import AbstractMessageQueue


class EventFetcherDependency(NonMonitorableDependencyProvider[AbstractMessageQueue, EventFetcher]):
    """Provides EventFetcher lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "event-fetcher"

    @asynccontextmanager
    async def provide(self, setup_input: AbstractMessageQueue) -> AsyncIterator[EventFetcher]:
        """Initialize and provide the event fetcher.

        Args:
            setup_input: The message queue to wrap

        Yields:
            Initialized EventFetcher
        """
        yield EventFetcher(setup_input)
