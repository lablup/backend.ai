from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import cast, override

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanContext, SpanKind, StatusCode

from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.events.types import (
    AbstractAnycastEvent,
    AbstractBroadcastEvent,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.message_queue.message import MQMessage
from ai.backend.common.message_queue.payload import AnycastMessagePayload, BroadcastMessagePayload
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.types import MessageName
from ai.backend.common.types import AgentId


class DummyAnycastEvent(AbstractAnycastEvent):
    value: int

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.AGENT

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "test_anycast"


class DummyBroadcastEvent(AbstractBroadcastEvent):
    value: int

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.AGENT

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "test_broadcast"


def _make_anycast_mq_message(event: AbstractAnycastEvent) -> MQMessage:
    message = event.to_message()
    return MQMessage(
        msg_id=b"test-msg-id",
        payload=AnycastMessagePayload(
            name=message.name,
            source="i-test",
            payload=message.payload,
        ),
    )


def _make_broadcast_payload(event: AbstractBroadcastEvent) -> BroadcastMessagePayload:
    message = event.to_message()
    return BroadcastMessagePayload(
        name=message.name,
        source="i-test",
        payload=message.payload,
    )


class StubMessageQueue:
    """A minimal stub that satisfies EventDispatcher's runtime usage."""

    def __init__(
        self,
        anycast_messages: list[MQMessage] | None = None,
        broadcast_messages: list[BroadcastMessagePayload] | None = None,
    ) -> None:
        self._anycast_messages = anycast_messages or []
        self._broadcast_messages = broadcast_messages or []
        self.done_calls: list[bytes] = []

    async def consume_queue(self) -> AsyncGenerator[MQMessage, None]:
        for msg in self._anycast_messages:
            yield msg

    async def subscribe_queue(self) -> AsyncGenerator[BroadcastMessagePayload, None]:
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
            broadcast_messages=[_make_broadcast_payload(DummyBroadcastEvent(value=7))],
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


class TestUndecodablePayload:
    """A body the handler's event class cannot validate is dropped, not retried forever.

    Redelivery cannot fix a payload that does not match the schema, so the message has to
    be acked — otherwise it occupies the stream until the retry limit discards it.
    """

    @pytest.fixture
    def received(self) -> list[DummyAnycastEvent]:
        return []

    @pytest.fixture
    def mq(self) -> StubMessageQueue:
        return StubMessageQueue(
            anycast_messages=[
                MQMessage(
                    msg_id=b"test-msg-id",
                    payload=AnycastMessagePayload(
                        name=MessageName(DummyAnycastEvent.event_name()),
                        source="i-test",
                        payload='{"value":"not-an-int"}',
                    ),
                )
            ],
        )

    @pytest.fixture
    async def dispatcher(
        self,
        mq: StubMessageQueue,
        received: list[DummyAnycastEvent],
    ) -> EventDispatcher:
        dispatcher = EventDispatcher(mq)  # type: ignore[arg-type]

        async def handler(ctx: object, source: AgentId, ev: DummyAnycastEvent) -> None:
            received.append(ev)

        dispatcher.consume(DummyAnycastEvent, object(), handler)
        return dispatcher

    async def test_handler_is_skipped_and_the_message_is_acked(
        self,
        dispatcher: EventDispatcher,
        mq: StubMessageQueue,
        received: list[DummyAnycastEvent],
    ) -> None:
        await dispatcher.start()
        await asyncio.sleep(0.1)
        await dispatcher.close()

        assert received == []
        assert mq.done_calls == [b"test-msg-id"]


class CapturingMessageQueue:
    """Keeps what the producer sends so it can be handed to a dispatcher."""

    sent: list[AnycastMessagePayload]

    def __init__(self) -> None:
        self.sent = []

    async def send(self, payload: AnycastMessagePayload) -> None:
        self.sent.append(payload)


async def _wait_for_span(exporter: InMemorySpanExporter, name: str) -> ReadableSpan:
    async def _poll() -> ReadableSpan:
        while True:
            for span in exporter.get_finished_spans():
                if span.name == name:
                    return span
            await asyncio.sleep(0.01)

    return await asyncio.wait_for(_poll(), timeout=5.0)


async def _dispatch_from_span(
    handler: Callable[[object, AgentId, DummyAnycastEvent], Coroutine[None, None, None]],
    exporter: InMemorySpanExporter,
) -> tuple[SpanContext, ReadableSpan]:
    """Produce the event inside a span, then dispatch it and return both sides' spans."""
    sent = CapturingMessageQueue()
    producer = EventProducer(cast(AbstractMessageQueue, sent), source=AgentId("i-test"))
    with trace.get_tracer(__name__).start_as_current_span("producer") as producer_span:
        await producer.anycast_event(DummyAnycastEvent(value=1))

    mq = StubMessageQueue(anycast_messages=[MQMessage(msg_id=b"test-msg-id", payload=sent.sent[0])])
    dispatcher = EventDispatcher(cast(AbstractMessageQueue, mq))
    dispatcher.consume(DummyAnycastEvent, object(), handler)
    await dispatcher.start()
    try:
        handler_span = await _wait_for_span(exporter, "test_anycast")
    finally:
        await dispatcher.close()
    return producer_span.get_span_context(), handler_span


class TestEventTraceContext:
    """The handler span joins the trace of the span that produced the event."""

    async def test_handler_span_is_child_of_producer_span(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        handler_trace_ids: list[int] = []

        async def handler(ctx: object, source: AgentId, ev: DummyAnycastEvent) -> None:
            handler_trace_ids.append(trace.get_current_span().get_span_context().trace_id)

        producer_context, handler_span = await _dispatch_from_span(handler, span_exporter)

        assert handler_trace_ids == [producer_context.trace_id]
        assert handler_span.kind == SpanKind.CONSUMER
        assert handler_span.parent is not None
        assert handler_span.parent.span_id == producer_context.span_id
        assert handler_span.status.status_code == StatusCode.UNSET

    async def test_failed_handler_marks_its_span_error(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        async def handler(ctx: object, source: AgentId, ev: DummyAnycastEvent) -> None:
            raise RuntimeError("handler failed")

        _, handler_span = await _dispatch_from_span(handler, span_exporter)

        assert handler_span.status.status_code == StatusCode.ERROR
        assert [event.name for event in handler_span.events] == ["exception"]
