from typing import Optional, Self, override

from ai.backend.common.events.types import AbstractEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent


class BaseScheduleEvent(AbstractEvent):
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
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoScheduleEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_schedule"


class DoCheckPrecondEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_check_precond"


class DoStartSessionEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_start_session"


class DoScaleEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_scale"
