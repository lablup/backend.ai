from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Self


class AbstractMQMessagePayload(ABC):
    @abstractmethod
    def serialize(self) -> dict[bytes, bytes]:
        raise NotImplementedError
    
    @abstractmethod
    @classmethod
    def deserialize(self, raw_event: dict[bytes, bytes]) -> Self:
        raise NotImplementedError


@dataclass
class MQMessage:
    msg_id: str
    payload: bytes


class AbstractMessageQueue(ABC):
    @abstractmethod
    async def send(
        self,
        key: str,
        msg: AbstractMQMessagePayload,
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
        msg: MQMessage,
    ) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...
