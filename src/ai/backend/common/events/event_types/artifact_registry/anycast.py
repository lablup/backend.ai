from typing import Any, Self, override

from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent


class DoScanReservoirRegistryEvent(AbstractAnycastEvent):
    """Event to trigger reservoir registry scanning."""

    def __init__(self) -> None:
        pass

    @override
    def serialize(self) -> tuple[Any, ...]:
        return ()

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls()

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_scan_reservoir_registry"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.ARTIFACT

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None
