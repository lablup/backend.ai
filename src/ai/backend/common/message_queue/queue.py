from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator

type MessageId = bytes
_DEFAULT_RETRY_FIELD = b"_retry_count"
_DEFAULT_MAX_RETRIES = 3


@dataclass
class MQMessage:
    msg_id: MessageId
    payload: dict[bytes, bytes]

    def retry(self) -> bool:
        """
        Retry the message.
        If the message has been retried more than the maximum number of retries,
        the message will be discarded.
        The retry count is stored in the message payload.
        """
        if self._retry_count() > _DEFAULT_MAX_RETRIES:
            return False
        self.payload[_DEFAULT_RETRY_FIELD] = str(self._retry_count() + 1).encode("utf-8")
        return True

    def _retry_count(self) -> int:
        """
        Get the retry count of the message.
        The retry count is the number of times the message has been re-delivered.
        """
        return int(self.payload.get(_DEFAULT_RETRY_FIELD, b"0"))


class AbstractMessageQueue(ABC):
    @abstractmethod
    async def send(
        self,
        payload: dict[bytes, bytes],
    ) -> None:
        """
        Send a message to the queue.

        If the queue is full, the oldest message will be removed.
        The new message will be added to the end of the queue.
        The message will be delivered to one consumer.
        """

    @abstractmethod
    async def consume_queue(
        self,
    ) -> AsyncGenerator[MQMessage, None]:
        """
        Consume messages from the queue.
        This method will block until a message is available.

        This is a normal queue, so the message will be delivered to one consumer.
        Messages are consumed only once by one consumer.
        """

    @abstractmethod
    async def subscribe_queue(
        self,
    ) -> AsyncGenerator[MQMessage, None]:
        """
        Subscribe to messages from the queue.
        This method will block until a message is available.

        This is a broadcast queue, so the message will be delivered to all subscribers.
        The subscriber should call `done` method to acknowledge the message when it is processed.
        """

    @abstractmethod
    async def done(
        self,
        msg_id: MessageId,
    ) -> None:
        """
        Acknowledge the message.

        This method should be called after the message is processed.
        If the consumer does not call `done`, the message will be re-delivered after the
        some timeout period.
        """

    @abstractmethod
    async def close(self) -> None:
        """
        Close the message queue.

        This method should be called when the message queue is no longer needed.
        It will close all connections and stop all background tasks.
        """
