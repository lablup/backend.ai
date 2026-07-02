from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.hub.hub import EventHub


class EventHubDependency(NonMonitorableDependencyProvider[None, EventHub]):
    """Provides EventHub lifecycle management."""

    @property
    @override
    def stage_name(self) -> str:
        return "event-hub"

    @asynccontextmanager
    @override
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
