import base64
from dataclasses import dataclass
from typing import Mapping, Self, cast

from ai.backend.common import msgpack

_DEFAULT_RETRY_FIELD = b"_retry_count"
_DEFAULT_MAX_RETRIES = 3

type MessageId = bytes


@dataclass
class BroadcastMessage:
    payload: Mapping[str, str]


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


@dataclass
class MessagePayload:
    name: str
    source: str
    args: tuple[bytes, ...]

    def serialize_anycast(self) -> Mapping[bytes, bytes]:
        """
        Serialize the message payload to a dictionary.
        """
        return {
            b"name": self.name.encode(),
            b"source": self.source.encode(),
            b"args": msgpack.packb(self.args),
        }

    def serialize_broadcast(self) -> Mapping[str, str]:
        """
        Serialize the message payload to a dictionary.
        The keys are bytes and the values are bytes.
        """
        args = base64.b64encode(msgpack.packb(self.args)).decode("ascii")
        return {
            "name": self.name,
            "source": self.source,
            "args": args,
        }

    @classmethod
    def from_anycast(cls, payload: Mapping[bytes, bytes]) -> Self:
        """
        Deserialize the message payload from a dictionary.
        The keys are bytes and the values are bytes.
        """
        return cls(
            name=payload[b"name"].decode("utf-8"),
            source=payload[b"source"].decode("utf-8"),
            args=cast(tuple[bytes, ...], msgpack.unpackb(payload[b"args"])),
        )

    @classmethod
    def from_broadcast(cls, payload: Mapping[str, str]) -> Self:
        """
        Deserialize the message payload from a dictionary.
        The keys are bytes and the values are bytes.
        """
        args_bytes = base64.b64decode(payload["args"])
        return cls(
            name=payload["name"],
            source=payload["source"],
            args=cast(tuple[bytes, ...], msgpack.unpackb(args_bytes)),
        )
