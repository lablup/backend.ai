from collections.abc import Mapping
from typing import Final, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ai.backend.common.json import dump_json, load_json

from .exceptions import InvalidMessagePayloadError
from .types import MessageMetadata, MessageName

# Wire field names.
_NAME_FIELD: Final[str] = "name"
_SOURCE_FIELD: Final[str] = "source"
_PAYLOAD_FIELD: Final[str] = "payload"
_METADATA_FIELD: Final[str] = "metadata"
_RETRY_COUNT_FIELD: Final[str] = "_retry_count"

# Errors any wire decoding may raise before the model itself is validated.
_DECODE_ERRORS: Final = (KeyError, TypeError, ValueError, ValidationError)


class AnycastMessagePayload(BaseModel):
    """
    A payload delivered to exactly one consumer, carried as the field mapping of a
    stream entry.

    `payload` is the JSON-serialized event body. It is opaque to this layer: what shape
    the body has is the event's business, not the transport's.

    `retry_count` is transport-level redelivery state maintained by the auto-claim
    path. Broadcast has no ack path, so it has no counterpart there.
    """

    model_config = ConfigDict(frozen=True)

    name: MessageName
    payload: str
    legacy_source: str = Field(validation_alias="source")
    metadata: MessageMetadata | None = None
    retry_count: int = 0

    @classmethod
    def from_event_body(
        cls,
        *,
        name: MessageName,
        source: str,
        payload: str,
        metadata: MessageMetadata | None = None,
    ) -> Self:
        """
        Build a payload out of the serialized body of an event.
        """
        return cls(name=name, source=source, payload=payload, metadata=metadata)

    def to_stream_fields(self) -> dict[bytes, bytes]:
        """
        Render the payload as the field mapping of a stream entry.
        """
        fields = {
            _NAME_FIELD.encode(): self.name.encode("utf-8"),
            _SOURCE_FIELD.encode(): self.legacy_source.encode("utf-8"),
            _PAYLOAD_FIELD.encode(): self.payload.encode("utf-8"),
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
                name=MessageName(fields[_NAME_FIELD.encode()].decode("utf-8")),
                source=fields[_SOURCE_FIELD.encode()].decode("utf-8"),
                payload=fields[_PAYLOAD_FIELD.encode()].decode("utf-8"),
                metadata=MessageMetadata.deserialize(raw_metadata) if raw_metadata else None,
                retry_count=int(raw_retry_count) if raw_retry_count else 0,
            )
        except (*_DECODE_ERRORS, UnicodeDecodeError) as e:
            raise InvalidMessagePayloadError(f"Malformed anycast message: {e}") from e

    def increment_retry(self) -> Self:
        return self.model_copy(update={"retry_count": self.retry_count + 1})


class BroadcastMessagePayload(BaseModel):
    """
    A payload delivered to every subscriber, carried as a JSON message on a channel.
    There is no ack, hence no retry state.

    `payload` is the JSON-serialized event body. It is opaque to this layer: what shape
    the body has is the event's business, not the transport's.
    """

    model_config = ConfigDict(frozen=True)

    name: MessageName
    payload: str
    legacy_source: str = Field(validation_alias="source")
    metadata: MessageMetadata | None = None

    @classmethod
    def from_event_body(
        cls,
        *,
        name: MessageName,
        source: str,
        payload: str,
        metadata: MessageMetadata | None = None,
    ) -> Self:
        """
        Build a payload out of the serialized body of an event.
        """
        return cls(name=name, source=source, payload=payload, metadata=metadata)

    def to_json(self) -> bytes:
        """
        Render the payload as the JSON message published to a channel.
        """
        fields = {
            _NAME_FIELD: self.name,
            _SOURCE_FIELD: self.legacy_source,
            _PAYLOAD_FIELD: self.payload,
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
                name=MessageName(fields[_NAME_FIELD]),
                source=fields[_SOURCE_FIELD],
                payload=fields[_PAYLOAD_FIELD],
                metadata=MessageMetadata.deserialize(raw_metadata) if raw_metadata else None,
            )
        except (*_DECODE_ERRORS, AttributeError) as e:
            raise InvalidMessagePayloadError(f"Malformed broadcast message: {e}") from e


class CachedBroadcastMessagePayload(BaseModel):
    """A broadcast payload, cached under `cache_id` when one is given."""

    model_config = ConfigDict(frozen=True)

    payload: BroadcastMessagePayload
    cache_id: str | None = None
