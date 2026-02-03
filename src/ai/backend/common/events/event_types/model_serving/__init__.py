from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Self, override

from ai.backend.common.events.types import AbstractEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import ModelServiceStatus, SessionId


@dataclass
class ModelServiceStatusEventArgs(AbstractEvent):
    session_id: SessionId
    new_status: ModelServiceStatus

    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.session_id),
            self.new_status.value,
        )

    @classmethod
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            session_id=SessionId(uuid.UUID(value[0])),
            new_status=ModelServiceStatus(value[1]),
        )

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_SERVING

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None
