import base64
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from typing import Iterator, Mapping, Optional, Self, cast

from ai.backend.common import msgpack
from ai.backend.common.contexts.request_id import with_request_id
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData
from ai.backend.common.json import dump_json, load_json
from ai.backend.logging.utils import with_log_context_fields

_DEFAULT_RETRY_FIELD = b"_retry_count"
_DEFAULT_MAX_RETRIES = 3

type MessageId = bytes


@dataclass
class BroadcastPayload:
    """Payload data for broadcasting with optional cache."""

    payload: Mapping[str, str]
    cache_id: Optional[str] = None


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
class MessageMetadata:
    request_id: Optional[str] = None
    user: Optional[UserData] = None

    def serialize(self) -> bytes:
        """
        Serialize the metadata to bytes.
        """
        return dump_json(self)

    @classmethod
    def deserialize(cls, data: str | bytes) -> Self:
        """
        Deserialize the metadata from bytes.
        """
        result = load_json(data)
        if "user_id" in result:
            del result["user_id"]
        if "user" in result:
            user_data = result["user"]
            if isinstance(user_data, dict):
                user = UserData(**user_data)
                result["user"] = user
            else:
                result["user"] = None
        return cls(**result)

    @contextmanager
    def apply_context(self) -> Iterator[None]:
        """
        Context manager to apply all context variables stored in metadata.
        """
        with ExitStack() as stack:
            log_fields: dict[str, str] = {}
            if self.request_id:
                stack.enter_context(with_request_id(self.request_id))
                log_fields["request_id"] = self.request_id
            if self.user:
                stack.enter_context(with_user(self.user))
                log_fields["user_id"] = str(self.user.user_id)
            if log_fields:
                stack.enter_context(with_log_context_fields(log_fields))
            yield


@dataclass
class MessagePayload:
    name: str
    source: str
    args: tuple[bytes, ...]
    metadata: Optional[MessageMetadata] = None

    def serialize_anycast(self) -> dict[bytes, bytes]:
        """
        Serialize the message payload to a dictionary.
        """
        result = {
            b"name": self.name.encode(),
            b"source": self.source.encode(),
            b"args": msgpack.packb(self.args),
        }
        if self.metadata:
            result[b"metadata"] = self.metadata.serialize()
        return result

    def serialize_broadcast(self) -> dict[str, str]:
        """
        Serialize the message payload to a dictionary.
        The keys are bytes and the values are bytes.
        """
        args = base64.b64encode(msgpack.packb(self.args)).decode("ascii")
        result = {
            "name": self.name,
            "source": self.source,
            "args": args,
        }
        if self.metadata:
            result["metadata"] = self.metadata.serialize().decode("utf-8")
        return result

    @classmethod
    def from_anycast(cls, payload: Mapping[bytes, bytes]) -> Self:
        """
        Deserialize the message payload from a dictionary.
        The keys are bytes and the values are bytes.
        """
        metadata = None
        if b"metadata" in payload:
            metadata = MessageMetadata.deserialize(payload[b"metadata"])
        return cls(
            name=payload[b"name"].decode("utf-8"),
            source=payload[b"source"].decode("utf-8"),
            args=cast(tuple[bytes, ...], msgpack.unpackb(payload[b"args"])),
            metadata=metadata,
        )

    @classmethod
    def from_broadcast(cls, payload: Mapping[str, str]) -> Self:
        """
        Deserialize the message payload from a dictionary.
        The keys are bytes and the values are bytes.
        """
        args_bytes = base64.b64decode(payload["args"])
        metadata = None
        if "metadata" in payload:
            metadata = MessageMetadata.deserialize(payload["metadata"])
        return cls(
            name=payload["name"],
            source=payload["source"],
            args=cast(tuple[bytes, ...], msgpack.unpackb(args_bytes)),
            metadata=metadata,
        )
