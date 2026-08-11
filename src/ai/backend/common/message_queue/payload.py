import base64
import binascii
from collections.abc import Mapping
from typing import Any, Final, Self, cast

from pydantic import BaseModel, ConfigDict, ValidationError

from ai.backend.common import msgpack
from ai.backend.common.json import dump_json, load_json

from .exceptions import InvalidMessagePayloadError
from .types import MessageMetadata

# Wire field names. The body is still carried as "args" until the producers cut over to JSON.
_NAME_FIELD: Final[str] = "name"
_SOURCE_FIELD: Final[str] = "source"
_BODY_FIELD: Final[str] = "args"
_METADATA_FIELD: Final[str] = "metadata"
_RETRY_COUNT_FIELD: Final[str] = "_retry_count"

# Errors any wire decoding may raise before the model itself is validated.
_DECODE_ERRORS: Final = (KeyError, TypeError, ValueError, ValidationError)


class MessagePayload(BaseModel):
    """
    The fields every message carries, regardless of delivery mode.

    `body` is opaque to this layer: it holds the serialized event arguments and is
    neither inspected nor decoded here.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    source: str
    body: bytes
    metadata: MessageMetadata | None = None

    @classmethod
    def from_event_args(
        cls,
        *,
        name: str,
        source: str,
        args: tuple[Any, ...],
        metadata: MessageMetadata | None = None,
    ) -> Self:
        """
        Build a payload out of the serializable arguments of an event.
        """
        return cls(name=name, source=source, body=msgpack.packb(args), metadata=metadata)

    def decode_args(self) -> tuple[Any, ...]:
        """
        Decode the event arguments carried by the body.
        """
        return cast(tuple[Any, ...], msgpack.unpackb(self.body))


class AnycastPayload(MessagePayload):
    """
    A payload delivered to exactly one consumer.

    `retry_count` is transport-level redelivery state maintained by the auto-claim
    path. It lives only here because broadcast has no ack path.
    """

    retry_count: int = 0

    def to_stream_fields(self) -> dict[bytes, bytes]:
        """
        Render the payload as the field mapping of a stream entry.
        """
        fields = {
            _NAME_FIELD.encode(): self.name.encode("utf-8"),
            _SOURCE_FIELD.encode(): self.source.encode("utf-8"),
            _BODY_FIELD.encode(): self.body,
        }
        if self.metadata is not None:
            fields[_METADATA_FIELD.encode()] = self.metadata.serialize()
        if self.retry_count:
            fields[_RETRY_COUNT_FIELD.encode()] = str(self.retry_count).encode("utf-8")
        return fields

    @classmethod
    def from_stream_fields(cls, fields: Mapping[bytes, bytes]) -> Self:
        """
        Build a payload out of the field mapping of a stream entry.

        Raises:
            InvalidMessagePayloadError: If the entry does not match the payload schema
        """
        raw_metadata = fields.get(_METADATA_FIELD.encode())
        raw_retry_count = fields.get(_RETRY_COUNT_FIELD.encode())
        try:
            return cls(
                name=fields[_NAME_FIELD.encode()].decode("utf-8"),
                source=fields[_SOURCE_FIELD.encode()].decode("utf-8"),
                body=fields[_BODY_FIELD.encode()],
                metadata=MessageMetadata.deserialize(raw_metadata) if raw_metadata else None,
                retry_count=int(raw_retry_count) if raw_retry_count else 0,
            )
        except _DECODE_ERRORS as e:
            raise InvalidMessagePayloadError(f"Malformed anycast message: {e}") from e

    def increment_retry(self) -> Self:
        return self.model_copy(update={"retry_count": self.retry_count + 1})


class BroadcastPayload(MessagePayload):
    """
    A payload delivered to every subscriber. There is no ack, hence no retry state.
    """

    def to_json(self) -> bytes:
        """
        Render the payload as the JSON message published to a channel.
        """
        fields = {
            _NAME_FIELD: self.name,
            _SOURCE_FIELD: self.source,
            _BODY_FIELD: base64.b64encode(self.body).decode("ascii"),
        }
        if self.metadata is not None:
            fields[_METADATA_FIELD] = self.metadata.serialize().decode("utf-8")
        return dump_json(fields)

    @classmethod
    def from_json(cls, data: str | bytes) -> Self:
        """
        Build a payload out of a JSON message received from a channel.

        Raises:
            InvalidMessagePayloadError: If the message does not match the payload schema
        """
        try:
            fields = load_json(data)
            raw_metadata = fields.get(_METADATA_FIELD)
            return cls(
                name=fields[_NAME_FIELD],
                source=fields[_SOURCE_FIELD],
                body=base64.b64decode(fields[_BODY_FIELD], validate=True),
                metadata=MessageMetadata.deserialize(raw_metadata) if raw_metadata else None,
            )
        except (*_DECODE_ERRORS, binascii.Error, AttributeError) as e:
            raise InvalidMessagePayloadError(f"Malformed broadcast message: {e}") from e


class CachedBroadcastPayload(BaseModel):
    """A broadcast payload, cached under `cache_id` when one is given."""

    model_config = ConfigDict(frozen=True)

    payload: BroadcastPayload
    cache_id: str | None = None
