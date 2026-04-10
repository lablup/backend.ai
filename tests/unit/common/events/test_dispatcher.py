from __future__ import annotations

import asyncio
import base64
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import msgpack
import pytest

from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.types import (
    AbstractAnycastEvent,
    AbstractBroadcastEvent,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.message_queue.types import (
    BroadcastMessage,
    MQMessage,
)
from ai.backend.common.types import AgentId


@dataclass
class DummyAnycastEvent(AbstractAnycastEvent):
    value: int

    def serialize(self) -> tuple[Any, ...]:
        return (self.value,)

    @classmethod
    def deserialize(cls, value: tuple[Any, ...]) -> DummyAnycastEvent:
        return cls(value[0])

    @classmethod
    def event_domain(cls) -> EventDomain:
        return EventDomain.AGENT

    def domain_id(self) -> str | None:
        return None

    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    def event_name(cls) -> str:
        return "test_anycast"


@dataclass
class DummyBroadcastEvent(AbstractBroadcastEvent):
    value: int

    def serialize(self) -> tuple[Any, ...]:
        return (self.value,)

    @classmethod
    def deserialize(cls, value: tuple[Any, ...]) -> DummyBroadcastEvent:
        return cls(value[0])

    @classmethod
    def event_domain(cls) -> EventDomain:
        return EventDomain.AGENT

    def domain_id(self) -> str | None:
        return None

    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    def event_name(cls) -> str:
        return "test_broadcast"


def _make_anycast_mq_message(event: AbstractAnycastEvent) -> MQMessage:
    return MQMessage(
        msg_id=b"test-msg-id",
        payload={
            b"name": event.event_name().encode("utf-8"),
            b"source": b"i-test",
            b"args": msgpack.packb(event.serialize()),
        },
    )


def _make_broadcast_message(event: AbstractBroadcastEvent) -> BroadcastMessage:
    args = base64.b64encode(msgpack.packb(event.serialize())).decode("ascii")
    return BroadcastMessage(
        payload={
            "name": event.event_name(),
            "source": "i-test",
            "args": args,
        },
    )


class StubMessageQueue:
    """A minimal stub that satisfies EventDispatcher's runtime usage."""

    def __init__(
        self,
        anycast_messages: list[MQMessage] | None = None,
        broadcast_messages: list[BroadcastMessage] | None = None,
    ) -> None:
        self._anycast_messages = anycast_messages or []
        self._broadcast_messages = broadcast_messages or []
        self.done_calls: list[bytes] = []

    async def consume_queue(self) -> AsyncGenerator[MQMessage, None]:
        for msg in self._anycast_messages:
            yield msg

    async def subscribe_queue(self) -> AsyncGenerator[BroadcastMessage, None]:
        for msg in self._broadcast_messages:
            yield msg

    async def done(self, msg_id: bytes) -> None:
        self.done_calls.append(msg_id)

    async def close(self) -> None:
        pass


class TestDispatchConsumers:
    """Tests for consumer dispatch with and without registered handlers."""

    @pytest.fixture
    def received(self) -> list[DummyAnycastEvent]:
        return []

    @pytest.fixture
    def mq(self) -> StubMessageQueue:
        return StubMessageQueue(
            anycast_messages=[_make_anycast_mq_message(DummyAnycastEvent(value=42))],
        )

    @pytest.fixture
    async def consumer_dispatcher(
        self,
        mq: StubMessageQueue,
        received: list[DummyAnycastEvent],
    ) -> EventDispatcher:
        dispatcher = EventDispatcher(mq)  # type: ignore[arg-type]

        async def handler(ctx: object, source: AgentId, ev: DummyAnycastEvent) -> None:
            received.append(ev)

        dispatcher.consume(DummyAnycastEvent, object(), handler)
        return dispatcher

    @pytest.fixture
    async def no_consumer_dispatcher(
        self,
        mq: StubMessageQueue,
    ) -> EventDispatcher:
        return EventDispatcher(mq)  # type: ignore[arg-type]

    async def test_registered_consumer_receives_event(
        self,
        consumer_dispatcher: EventDispatcher,
        received: list[DummyAnycastEvent],
    ) -> None:
        await consumer_dispatcher.start()
        await asyncio.sleep(0.1)
        await consumer_dispatcher.close()

        assert len(received) == 1
        assert received[0].value == 42

    async def test_no_error_when_no_consumer_registered(
        self,
        no_consumer_dispatcher: EventDispatcher,
        mq: StubMessageQueue,
    ) -> None:
        await no_consumer_dispatcher.start()
        await asyncio.sleep(0.1)
        await no_consumer_dispatcher.close()

        assert mq.done_calls == [b"test-msg-id"]


class TestDispatchSubscribers:
    """Tests for subscriber dispatch with and without registered handlers."""

    @pytest.fixture
    def received(self) -> list[DummyBroadcastEvent]:
        return []

    @pytest.fixture
    def mq(self) -> StubMessageQueue:
        return StubMessageQueue(
            broadcast_messages=[_make_broadcast_message(DummyBroadcastEvent(value=7))],
        )

    @pytest.fixture
    async def subscriber_dispatcher(
        self,
        mq: StubMessageQueue,
        received: list[DummyBroadcastEvent],
    ) -> EventDispatcher:
        dispatcher = EventDispatcher(mq)  # type: ignore[arg-type]

        async def handler(ctx: object, source: AgentId, ev: DummyBroadcastEvent) -> None:
            received.append(ev)

        dispatcher.subscribe(DummyBroadcastEvent, object(), handler)
        return dispatcher

    @pytest.fixture
    async def no_subscriber_dispatcher(
        self,
        mq: StubMessageQueue,
    ) -> EventDispatcher:
        return EventDispatcher(mq)  # type: ignore[arg-type]

    async def test_registered_subscriber_receives_event(
        self,
        subscriber_dispatcher: EventDispatcher,
        received: list[DummyBroadcastEvent],
    ) -> None:
        await subscriber_dispatcher.start()
        await asyncio.sleep(0.1)
        await subscriber_dispatcher.close()

        assert len(received) == 1
        assert received[0].value == 7

    async def test_no_error_when_no_subscriber_registered(
        self,
        no_subscriber_dispatcher: EventDispatcher,
    ) -> None:
        await no_subscriber_dispatcher.start()
        await asyncio.sleep(0.1)
        await no_subscriber_dispatcher.close()
