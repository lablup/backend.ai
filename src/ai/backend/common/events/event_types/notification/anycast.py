from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, override

from pydantic import Field

from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import BackendAISchema

__all__ = ("NotificationTriggeredEvent",)


class NotificationTriggeredEvent(BackendAISchema, AbstractAnycastEvent):
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
