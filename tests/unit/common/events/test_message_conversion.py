from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.events.event_types.notification.anycast import NotificationTriggeredEvent
from ai.backend.common.events.exceptions import (
    EventPayloadDecodingError,
    EventPayloadEncodingError,
)
from ai.backend.common.events.message import EventMessage
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.message_queue.types import MessageName


class _Opaque:
    """A value no JSON encoder knows how to render."""


class DummyEvent(AbstractAnycastEvent):
    model_config = {"arbitrary_types_allowed": True}

    value: int = 0
    blob: Any = None

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.AGENT

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "test_message_conversion"


class TestToMessage:
    def test_unserializable_field_raises_the_event_error(self) -> None:
        with pytest.raises(EventPayloadEncodingError):
            DummyEvent(blob=_Opaque()).to_message()


class TestFromMessage:
    @pytest.mark.parametrize(
        "payload",
        ['{"value":"not-an-int"}', "{", "null"],
        ids=["wrong_field_type", "malformed_json", "not_an_object"],
    )
    def test_unreadable_body_raises_the_event_error(self, payload: str) -> None:
        message = EventMessage(name=MessageName(DummyEvent.event_name()), payload=payload)

        with pytest.raises(EventPayloadDecodingError):
            DummyEvent.from_message(message)

    def test_backendai_schema_event_raises_the_same_error(self) -> None:
        """An event deriving `BackendAISchema` maps `ValidationError` to its own
        `BackendAIError`, so the event layer has to funnel that form in too."""
        message = EventMessage(
            name=MessageName(NotificationTriggeredEvent.event_name()),
            payload='{"rule_type":"session.started"}',  # missing `timestamp`
        )

        with pytest.raises(EventPayloadDecodingError):
            NotificationTriggeredEvent.from_message(message)

    def test_roundtrip_is_unaffected(self) -> None:
        event = NotificationTriggeredEvent(
            rule_type="session.started",
            timestamp=datetime(2026, 8, 12, tzinfo=UTC),
            notification_data={"session_id": "abc"},
        )

        assert NotificationTriggeredEvent.from_message(event.to_message()) == event
