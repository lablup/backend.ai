from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator

from ..types import MessageId, MQMessage


class AbstractConsumer(ABC):
    """
    Abstract interface for consuming messages from queues with acknowledgment.
    Supports consumer groups and automatic retry/recovery mechanisms.
    """

    @abstractmethod
    async def consume_queue(self) -> AsyncGenerator[MQMessage, None]:
        """
        Consume messages from the queue.

        This is a generator that yields messages as they become available.
        Each message should be acknowledged using the done() method.

        Yields:
            MQMessage: Messages from the queue

        Raises:
            RuntimeError: If the component is closed
        """
        raise NotImplementedError

    @abstractmethod
    async def done(self, msg_id: MessageId) -> None:
        """
        Acknowledge that a message has been processed successfully.

        Args:
            msg_id: The message identifier to acknowledge

        Raises:
            RuntimeError: If the component is closed
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Close the consumer and cleanup resources.
        """
        raise NotImplementedError
