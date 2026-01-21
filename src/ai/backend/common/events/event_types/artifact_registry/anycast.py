from typing import Optional, Self, override

from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent


class DoScanReservoirRegistryEvent(AbstractAnycastEvent):
    """Event to trigger reservoir registry scanning."""

    def __init__(self) -> None:
        pass

    @override
    def serialize(self) -> tuple:
        return ()

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
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
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None
