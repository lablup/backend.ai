from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator

type MessageId = str


@dataclass
class MQMessage:
    msg_id: MessageId
    payload: dict[bytes, bytes]


class AbstractMessageQueue(ABC):
    @abstractmethod
    async def send(
        self,
        key: str,
        payload: dict[bytes, bytes],
    ) -> None: ...

    @abstractmethod
    async def consume_queue(
        self,
    ) -> AsyncGenerator[MQMessage, None]: ...

    @abstractmethod
    async def subscribe_queue(
        self,
    ) -> AsyncGenerator[MQMessage, None]:
        """
        Subscribe to the message queue.
        """

    @abstractmethod
    async def done(
        self,
        msg_id: MessageId,
    ) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...
