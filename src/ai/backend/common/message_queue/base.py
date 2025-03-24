from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Self


class AbstractMQMessagePayload(ABC):
    @abstractmethod
    def serialize(self) -> dict[bytes, bytes]:
        result: dict[bytes, bytes] = {}
        for key, value in self.__dict__.items():
            key_bytes = str(key).encode("utf-8")
            value_bytes = value if isinstance(value, bytes) else str(value).encode("utf-8")
            result[key_bytes] = value_bytes
        return result

    @abstractmethod
    @classmethod
    def deserialize(cls, raw_event: dict[bytes, bytes]) -> Self:
        kwargs = {key.decode("utf-8"): value.decode("utf-8") for key, value in raw_event.items()}
        return cls(**kwargs)


@dataclass
class MQMessage:
    msg_id: str
    payload: AbstractMQMessagePayload


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
