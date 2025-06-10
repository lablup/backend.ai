from __future__ import annotations

from typing import Optional, Self, override

from ai.backend.common.events.types import (
    AbstractAnycastEvent,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent


class DoLogCleanupEvent(AbstractAnycastEvent):
    @override
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    def deserialize(cls, data: tuple) -> Self:
        return cls()

    @classmethod
    def event_domain(self) -> EventDomain:
        return EventDomain.LOG

    def domain_id(self) -> Optional[str]:
        return None

    def user_event(self) -> Optional[UserEvent]:
        return None

    @classmethod
    def event_name(cls) -> str:
        return "do_log_cleanup"
