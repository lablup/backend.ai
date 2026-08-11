from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Self, override

from pydantic import Field

from ai.backend.common.events.payload import AnycastEventPayload
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.common.types import BackendAISchema

__all__ = ("NotificationTriggeredEvent", "NotificationTriggeredEventPayload")


class NotificationTriggeredEventPayload(AnycastEventPayload):
    rule_type: str
    timestamp: datetime
    notification_data: Mapping[str, Any] = Field(default_factory=dict)


class NotificationTriggeredEvent(
    BackendAISchema, AbstractAnycastEvent[NotificationTriggeredEventPayload]
):
    """
    Event triggered when a notification needs to be processed.
    This is an anycast event ensuring only one handler processes each notification.
    """

    rule_type: str = Field(
        description=(
            "Type identifier for matching notification rules. "
            "Notification rules are configured to match specific rule types. "
            "Examples: 'session.started', 'agent.terminated', 'quota.exceeded', 'user.registered'"
        )
    )
    timestamp: datetime = Field(description="When the notification event occurred")
    notification_data: Mapping[str, Any] = Field(
        default_factory=dict,
        description=(
            "Data to be used in notification message. "
            "This contains all information needed for template rendering and filtering. "
            "For example: {'session_id': 'xxx', 'user': 'john', 'status': 'terminated'}"
        ),
    )

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.NOTIFICATION

    @classmethod
    @override
    def event_name(cls) -> str:
        return "notification_triggered"

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None

    @override
    def to_payload(self) -> NotificationTriggeredEventPayload:
        return NotificationTriggeredEventPayload(
            rule_type=self.rule_type,
            timestamp=self.timestamp,
            notification_data=self.notification_data,
        )

    @classmethod
    @override
    def from_payload(cls, payload: NotificationTriggeredEventPayload) -> Self:
        return cls(
            rule_type=payload.rule_type,
            timestamp=payload.timestamp,
            notification_data=payload.notification_data,
        )

    @override
    def serialize(self) -> tuple[bytes, ...]:
        return (
            self.rule_type.encode(),
            self.timestamp.isoformat().encode(),
            dump_json_str(self.notification_data).encode(),
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[bytes, ...]) -> NotificationTriggeredEvent:
        return cls(
            rule_type=value[0].decode(),
            timestamp=datetime.fromisoformat(value[1].decode()),
            notification_data=load_json(value[2]),
        )
