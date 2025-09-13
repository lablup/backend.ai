from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator

from ..types import BroadcastMessage


class AbstractSubscriber(ABC):
    """
    Abstract interface for subscribing to broadcast messages.
    Receives messages sent via broadcast channels.
    """

    @abstractmethod
    async def subscribe_queue(self) -> AsyncGenerator[BroadcastMessage, None]:
        """
        Subscribe to broadcast messages.

        This is a generator that yields broadcast messages as they arrive.
        Unlike consumer messages, broadcast messages don't require acknowledgment.

        Yields:
            BroadcastMessage: Broadcast messages from subscribed channels

        Raises:
            RuntimeError: If the component is closed
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Close the subscriber and cleanup resources.
        """
        raise NotImplementedError
