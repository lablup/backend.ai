"""Abstract base class for notification channels."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import NotificationMessage, SendResult

__all__ = ("AbstractNotificationChannel",)


class AbstractNotificationChannel(ABC):
    """Abstract base class for notification channel handlers."""

    @abstractmethod
    async def send(
        self,
        message: NotificationMessage,
    ) -> SendResult:
        """
        Send notification through this channel.

        Args:
            message: Notification message to send

        Returns:
            SendResult indicating success or failure
        """
        raise NotImplementedError
