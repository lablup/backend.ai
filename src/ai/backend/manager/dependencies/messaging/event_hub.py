from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.hub.hub import EventHub


class EventHubDependency(NonMonitorableDependencyProvider[None, EventHub]):
    """Provides EventHub lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "event-hub"

    @asynccontextmanager
    async def provide(self, setup_input: None) -> AsyncIterator[EventHub]:
        """Initialize and provide the event hub.

        Args:
            setup_input: None (EventHub has no dependencies)

        Yields:
            Initialized EventHub
        """
        event_hub = EventHub()
        try:
            yield event_hub
        finally:
            await event_hub.shutdown()
