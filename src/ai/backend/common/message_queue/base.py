import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, Generic, Literal, Optional, Self, TypeVar

import msgpack

from ai.backend.common.types import BaseConnectionInfo


@dataclass
class MQMessage:
    topic: str
    payload: Dict[bytes, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def serialize(self, format: str = "msgpack") -> bytes:
        message = {
            "topic": self.topic,
            "payload": self.payload,
            "metadata": self.metadata,
        }

        if format == "msgpack":
            result = msgpack.dumps(message, use_bin_type=True)
            if result is None:
                raise ValueError("msgpack.dumps returned None")
            return result
        elif format == "json":
            return json.dumps(message).encode("utf-8")
        else:
            raise ValueError(f"Unsupported serialization format: {format}")

    @classmethod
    def deserialize(cls, data: bytes, format: Literal["msgpack", "json"] = "msgpack") -> Self:
        if format == "msgpack":
            message = msgpack.unpackb(data)
        elif format == "json":
            message = json.loads(data.decode("utf-8"))
        else:
            raise ValueError(f"Unsupported serialization format: {format}")

        decoded_payload = {k: v if isinstance(v, bytes) else str(v).encode() for k, v in message["payload"].items()}

        return cls(topic=message["topic"], payload=decoded_payload, metadata=message["metadata"])

T = TypeVar("T", bound=BaseConnectionInfo)

class AbstractMessageQueue(ABC, Generic[T]):
    connection_info: T

    @abstractmethod
    async def receive(
        self,
        stream_key: str,
        *,
        block_timeout: int = 10_000,  # in msec
    ) -> AsyncGenerator[MQMessage, None]:...

    @abstractmethod
    async def receive_group(
        self,
        stream_key: str,
        group_name: str,
        consumer_id: str,
        *,
        autoclaim_idle_timeout: int = 1_000,  # in msec
        block_timeout: int = 10_000,  # in msec
    ) -> AsyncGenerator[MQMessage, None]: ...

    @abstractmethod
    async def send(
        self,
        msg: MQMessage,
        *,
        is_flush: bool = False,
        service_name: Optional[str] = None,
        encoding: Optional[str] = None,
        command_timeout: Optional[float] = None,
    ) -> None: ...

    @abstractmethod
    async def close(self, close_connection_pool: Optional[bool] = None) -> None: ...
