from __future__ import annotations

from typing import Any, Self, override

from ai.backend.common.events.types import (
    AbstractAnycastEvent,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent


class DoLogCleanupEvent(AbstractAnycastEvent):
    @override
    def serialize(self) -> tuple[Any, ...]:
        return tuple()

    @classmethod
    def deserialize(cls, value: tuple[Any, ...]) -> Self:  # noqa: ARG003
        return cls()

    @classmethod
    def event_domain(cls) -> EventDomain:
        return EventDomain.LOG

    def domain_id(self) -> str | None:
        return None

    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    def event_name(cls) -> str:
        return "do_log_cleanup"
