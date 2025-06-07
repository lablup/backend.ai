from typing import Optional, Self, override

from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent


class BaseIdleCheckEvent(AbstractAnycastEvent):
    @override
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls()

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.IDLE_CHECK

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoIdleCheckEvent(BaseIdleCheckEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_idle_check"
