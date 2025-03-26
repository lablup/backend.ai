from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator

type MessageId = bytes


@dataclass
class MQMessage:
    msg_id: MessageId
    payload: dict[bytes, bytes]


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
