from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.manager.notification.notification_center import NotificationCenter

from .base import DomainDependency


class NotificationCenterDependency(DomainDependency[None, NotificationCenter]):
    """Provides NotificationCenter lifecycle management.

    NotificationCenter manages HTTP client pools for sending notifications.
    It has no external dependencies and creates its own internal resources.
    """

    @property
    def stage_name(self) -> str:
        return "notification-center"

    @asynccontextmanager
    async def provide(self, setup_input: None) -> AsyncIterator[NotificationCenter]:
        """Initialize and provide a NotificationCenter.

        Args:
            setup_input: Not used (None). NotificationCenter has no dependencies.

        Yields:
            Initialized NotificationCenter instance.
        """
        notification_center = NotificationCenter()
        try:
            yield notification_center
        finally:
            await notification_center.close()
