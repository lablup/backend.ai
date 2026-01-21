from __future__ import annotations

import uuid
from typing import Optional, Self
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.events.hub import WILDCARD, EventHub, EventPropagator
from ai.backend.common.events.types import AbstractEvent, DeliveryPattern, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent


class DummyBaseEvent(AbstractEvent):
    def __init__(self, domain_id: str) -> None:
        self._domain_id = domain_id

    def domain_id(self) -> Optional[str]:
        return self._domain_id

    @classmethod
    def delivery_pattern(cls) -> DeliveryPattern:
        return DeliveryPattern.BROADCAST

    def serialize(self) -> tuple[bytes, ...]:
        raise NotImplementedError

    @classmethod
    def deserialize(cls, value: tuple[bytes, ...]) -> Self:
        raise NotImplementedError

    @classmethod
    def event_name(cls) -> str:
        return "dummy"

    def user_event(self) -> Optional[UserEvent]:
        return None


class DummySessionEvent(DummyBaseEvent):
    @classmethod
    def event_domain(cls) -> EventDomain:
        return EventDomain.SESSION


class DummyKernelEvent(DummyBaseEvent):
    @classmethod
    def event_domain(cls) -> EventDomain:
        return EventDomain.KERNEL


class DummyEventPropagator(EventPropagator):
    records: list[str]

    def __init__(self) -> None:
        self._id = uuid.uuid4()
        self.records = []

    def id(self) -> uuid.UUID:
        return self._id

    async def propagate_event(self, event: AbstractEvent) -> None:
        self.records.append(event.domain_id() or "")

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_hub_normal_aliases():
    hub = EventHub()
    aliases = [
        (EventDomain.SESSION, "s001"),
        (EventDomain.SESSION, "s002"),
        (EventDomain.SESSION, "s003"),
    ]
    propagator1 = DummyEventPropagator()
    hub.register_event_propagator(propagator1, aliases)
    aliases = [
        (EventDomain.SESSION, "s004"),
        (EventDomain.SESSION, "s005"),
    ]
    propagator2 = DummyEventPropagator()
    hub.register_event_propagator(propagator2, aliases)

    await hub.propagate_event(DummySessionEvent("s001"))
    await hub.propagate_event(DummySessionEvent("s001"))
    await hub.propagate_event(DummySessionEvent("s004"))
    await hub.propagate_event(DummyKernelEvent("k102"))  # skipped
    await hub.propagate_event(DummyKernelEvent("k103"))  # skipped

    hub.unregister_event_propagator(propagator1.id())
    assert (EventDomain.SESSION, "s001") not in hub._key_alias
    assert (EventDomain.SESSION, "s002") not in hub._key_alias
    assert (EventDomain.SESSION, "s003") not in hub._key_alias
    assert (EventDomain.SESSION, "s004") in hub._key_alias
    assert (EventDomain.SESSION, "s005") in hub._key_alias

    await hub.propagate_event(DummySessionEvent("s002"))  # skipped
    await hub.propagate_event(DummyKernelEvent("k101"))  # skipped
    await hub.propagate_event(DummySessionEvent("s005"))

    assert propagator1.records == [
        "s001",
        "s001",
    ]
    assert propagator2.records == [
        "s004",
        "s005",
    ]


@pytest.mark.asyncio
async def test_hub_wildcard_aliases():
    hub = EventHub()
    aliases = [
        (EventDomain.SESSION, WILDCARD),
    ]
    propagator1 = DummyEventPropagator()
    hub.register_event_propagator(propagator1, aliases)
    aliases = [
        (EventDomain.SESSION, "s004"),
        (EventDomain.SESSION, "s005"),
    ]
    propagator2 = DummyEventPropagator()
    hub.register_event_propagator(propagator2, aliases)

    await hub.propagate_event(DummySessionEvent("s001"))
    await hub.propagate_event(DummySessionEvent("s001"))
    await hub.propagate_event(DummySessionEvent("s003"))
    await hub.propagate_event(DummySessionEvent("s004"))  # sent to both propagators
    await hub.propagate_event(DummyKernelEvent("k102"))  # skipped
    await hub.propagate_event(DummyKernelEvent("k103"))  # skipped

    hub.unregister_event_propagator(propagator1.id())
    assert EventDomain.SESSION not in hub._wildcard_alias
    assert (EventDomain.SESSION, "s004") in hub._key_alias
    assert (EventDomain.SESSION, "s005") in hub._key_alias

    await hub.propagate_event(DummySessionEvent("s002"))  # skipped
    await hub.propagate_event(DummyKernelEvent("k101"))  # skipped
    await hub.propagate_event(DummySessionEvent("s005"))

    assert propagator1.records == [
        "s001",
        "s001",
        "s003",
        "s004",
    ]
    assert propagator2.records == [
        "s004",
        "s005",
    ]


@pytest.mark.asyncio
async def test_hub_close_by_alias():
    hub = EventHub()
    aliases = [
        (EventDomain.SESSION, WILDCARD),
    ]
    propagator1 = DummyEventPropagator()
    propagator1.close = AsyncMock()
    hub.register_event_propagator(propagator1, aliases)
    aliases = [
        (EventDomain.SESSION, "s004"),
        (EventDomain.SESSION, "s005"),
    ]
    propagator2 = DummyEventPropagator()
    propagator2.close = AsyncMock()
    hub.register_event_propagator(propagator2, aliases)

    await hub.close_by_alias(EventDomain.SESSION, WILDCARD)

    # WILDCARD does not mean closing of all propagators,
    # but closing of propagators registered using WILDCARD.
    propagator1.close.assert_awaited_once()
    propagator2.close.assert_not_awaited()

    # Closing with each domain ID calls close() individually.
    await hub.close_by_alias(EventDomain.SESSION, "s004")
    await hub.close_by_alias(EventDomain.SESSION, "s005")
    assert propagator2.close.await_count == 2


@pytest.mark.asyncio
async def test_hub_shutdown():
    hub = EventHub()
    aliases = [
        (EventDomain.SESSION, WILDCARD),
    ]
    propagator1 = DummyEventPropagator()
    propagator1.close = AsyncMock()
    hub.register_event_propagator(propagator1, aliases)
    aliases = [
        (EventDomain.SESSION, "s004"),
        (EventDomain.SESSION, "s005"),
    ]
    propagator2 = DummyEventPropagator()
    propagator2.close = AsyncMock()
    hub.register_event_propagator(propagator2, aliases)

    await hub.shutdown()

    # All propagators should now be closed.
    propagator1.close.assert_awaited_once()
    propagator2.close.assert_awaited_once()
