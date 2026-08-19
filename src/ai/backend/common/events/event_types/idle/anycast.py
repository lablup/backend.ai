from typing import override

from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent


class BaseIdleCheckEvent(AbstractAnycastEvent):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.IDLE_CHECK

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoIdleCheckEvent(BaseIdleCheckEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_idle_check"
