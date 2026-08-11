from typing import Any, Self, override

from ai.backend.common.events.payload import AnycastEventPayload
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent


class IdleCheckEventPayload(AnycastEventPayload):
    """An idle check carries no arguments: the event itself is the whole message."""


class BaseIdleCheckEvent(AbstractAnycastEvent[IdleCheckEventPayload]):
    @override
    def serialize(self) -> tuple[Any, ...]:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls()

    @override
    def to_payload(self) -> IdleCheckEventPayload:
        return IdleCheckEventPayload()

    @classmethod
    @override
    def from_payload(cls, payload: IdleCheckEventPayload) -> Self:
        return cls()

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
