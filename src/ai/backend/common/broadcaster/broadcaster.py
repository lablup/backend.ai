from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator


@dataclass
class BroadcastedMessage:
    """
    Broadcasted message.
    The message is a dictionary of bytes.
    The message is delivered to all subscribers.
    """

    payload: bytes


class AbstractBroadcastSubscriber(ABC):
    """
    Abstract class for a subscriber.
    A subscriber subscribes to messages from broadcaster.
    """

    @abstractmethod
    async def subscribe_queue(
        self,
    ) -> AsyncGenerator[BroadcastedMessage, None]:
        """
        Subscribe to messages from broadcaster.
        This method will block until a message is available.
        """
        raise NotImplementedError("Subscribe queue method not implemented")

    @abstractmethod
    async def close(self) -> None:
        """
        Close the subscriber.
        This method should be called after the subscriber is no longer needed.
        """
        raise NotImplementedError("Close method not implemented")


class AbstractBroadcaster(ABC):
    """
    Abstract class for a broadcaster.
    A broadcaster broadcasts messages to all subscribers.
    The message will be delivered to all subscribers.
    """

    async def broadcast(self, payload: bytes) -> None:
        """
        Broadcast a message to all consumers.
        """
        raise NotImplementedError("Broadcast method not implemented")
