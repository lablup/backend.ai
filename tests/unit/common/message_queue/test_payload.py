from __future__ import annotations

import pytest

from ai.backend.common.message_queue.exceptions import InvalidMessagePayloadError
from ai.backend.common.message_queue.payload import (
    AnycastMessagePayload,
    BroadcastMessagePayload,
)
from ai.backend.common.message_queue.types import MessageMetadata, MessageName

_PAYLOAD = '{"value":42}'


class TestAnycastMessagePayload:
    @pytest.fixture
    def payload(self) -> AnycastMessagePayload:
        return AnycastMessagePayload.from_event_body(
            name=MessageName("test_event"),
            source="i-test",
            payload=_PAYLOAD,
            metadata=MessageMetadata(request_id="req-1"),
        )

    def test_stream_fields_roundtrip(self, payload: AnycastMessagePayload) -> None:
        assert AnycastMessagePayload.from_stream_fields(payload.to_stream_fields()) == payload

    def test_retry_count_survives_the_roundtrip(self, payload: AnycastMessagePayload) -> None:
        retried = payload.increment_retry()
        restored = AnycastMessagePayload.from_stream_fields(retried.to_stream_fields())
        assert restored.retry_count == 1

    def test_entry_without_a_payload_field_is_rejected(self) -> None:
        with pytest.raises(InvalidMessagePayloadError):
            AnycastMessagePayload.from_stream_fields({
                b"name": b"test_event",
                b"source": b"i-test",
            })


class TestBroadcastMessagePayload:
    @pytest.fixture
    def payload(self) -> BroadcastMessagePayload:
        return BroadcastMessagePayload.from_event_body(
            name=MessageName("test_event"),
            source="i-test",
            payload=_PAYLOAD,
            metadata=MessageMetadata(request_id="req-1"),
        )

    def test_json_roundtrip(self, payload: BroadcastMessagePayload) -> None:
        assert BroadcastMessagePayload.from_json(payload.to_json()) == payload

    def test_message_without_a_payload_field_is_rejected(self) -> None:
        with pytest.raises(InvalidMessagePayloadError):
            BroadcastMessagePayload.from_json(b'{"name":"test_event","source":"i-test"}')

    def test_malformed_json_is_rejected(self) -> None:
        with pytest.raises(InvalidMessagePayloadError):
            BroadcastMessagePayload.from_json(b"not json")
