import asyncio
from dataclasses import dataclass
from types import TracebackType
from typing import Optional, Type

import aiotools
import pytest

from ai.backend.common.events.dispatcher import (
    CoalescingOptions,
    CoalescingState,
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.events.types import (
    AbstractBroadcastEvent,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import AgentId


@dataclass
class DummyBroadcastEvent(AbstractBroadcastEvent):
    value: int

    def serialize(self) -> tuple:
        return (self.value + 1,)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0] + 1)

    @classmethod
    def event_domain(self) -> EventDomain:
        return EventDomain.AGENT

    def domain_id(self) -> Optional[str]:
        return None

    def user_event(self) -> Optional[UserEvent]:
        return None

    @classmethod
    def event_name(self) -> str:
        return "testing"


EVENT_DISPATCHER_CONSUMER_GROUP = "test"


@pytest.mark.asyncio
async def test_dispatch(test_valkey_stream_mq, test_node_id) -> None:
    app = object()

    dispatcher = EventDispatcher(
        test_valkey_stream_mq,
    )
    producer = EventProducer(test_valkey_stream_mq, source=AgentId(test_node_id))

    records = set()

    async def acb(context: object, source: AgentId, event: DummyBroadcastEvent) -> None:
        assert context is app
        assert source == AgentId("i-test")
        assert isinstance(event, DummyBroadcastEvent)
        assert event.event_name() == "testing"
        assert event.value == 1001
        await asyncio.sleep(0.01)
        records.add("async")

    def scb(context: object, source: AgentId, event: DummyBroadcastEvent) -> None:
        assert context is app
        assert source == AgentId("i-test")
        assert isinstance(event, DummyBroadcastEvent)
        assert event.event_name() == "testing"
        assert event.value == 1001
        records.add("sync")

    dispatcher.subscribe(DummyBroadcastEvent, app, acb)
    dispatcher.subscribe(DummyBroadcastEvent, app, scb)
    await dispatcher.start()
    await asyncio.sleep(0.1)

    # Dispatch the event
    await producer.broadcast_event(DummyBroadcastEvent(999), source_override=AgentId("i-test"))
    await asyncio.sleep(0.2)
    assert records == {"async", "sync"}

    await producer.close()
    await dispatcher.close()


@pytest.mark.asyncio
async def test_error_on_dispatch(test_valkey_stream_mq, test_node_id) -> None:
    app = object()
    exception_log: list[str] = []

    async def handle_exception(
        et: Type[Exception],
        exc: Exception,
        tb: TracebackType,
    ) -> None:
        exception_log.append(type(exc).__name__)

    dispatcher = EventDispatcher(
        test_valkey_stream_mq,
        consumer_exception_handler=handle_exception,  # type: ignore
        subscriber_exception_handler=handle_exception,  # type: ignore
    )
    producer = EventProducer(test_valkey_stream_mq, source=AgentId(test_node_id))

    async def acb(context: object, source: AgentId, event: DummyBroadcastEvent) -> None:
        assert context is app
        assert source == AgentId("i-test")
        assert isinstance(event, DummyBroadcastEvent)
        raise ZeroDivisionError

    def scb(context: object, source: AgentId, event: DummyBroadcastEvent) -> None:
        assert context is app
        assert source == AgentId("i-test")
        assert isinstance(event, DummyBroadcastEvent)
        raise OverflowError

    dispatcher.subscribe(DummyBroadcastEvent, app, scb)
    dispatcher.subscribe(DummyBroadcastEvent, app, acb)
    await dispatcher.start()
    await asyncio.sleep(0.1)

    await producer.broadcast_event(DummyBroadcastEvent(0), source_override=AgentId("i-test"))
    await asyncio.sleep(0.5)
    assert len(exception_log) == 2
    assert "ZeroDivisionError" in exception_log
    assert "OverflowError" in exception_log

    await producer.close()
    await dispatcher.close()


@pytest.mark.asyncio
async def test_event_dispatcher_rate_control():
    opts = CoalescingOptions(max_wait=0.1, max_batch_size=5)
    state = CoalescingState()
    assert await state.rate_control(None) is True
    epsilon = 0.01
    clock = aiotools.VirtualClock()
    with clock.patch_loop():
        for _ in range(2):  # repetition should not affect the behavior
            t1 = asyncio.create_task(state.rate_control(opts))
            await asyncio.sleep(0.1 + epsilon)
            assert t1.result() is True

            t1 = asyncio.create_task(state.rate_control(opts))
            t2 = asyncio.create_task(state.rate_control(opts))
            t3 = asyncio.create_task(state.rate_control(opts))
            await asyncio.sleep(0.1 + epsilon)
            assert t1.result() is False
            assert t2.result() is False
            assert t3.result() is True

            t1 = asyncio.create_task(state.rate_control(opts))
            await asyncio.sleep(0.1 + epsilon)
            t2 = asyncio.create_task(state.rate_control(opts))
            await asyncio.sleep(0.1 + epsilon)
            assert t1.result() is True
            assert t2.result() is True

            t1 = asyncio.create_task(state.rate_control(opts))
            t2 = asyncio.create_task(state.rate_control(opts))
            t3 = asyncio.create_task(state.rate_control(opts))
            t4 = asyncio.create_task(state.rate_control(opts))
            t5 = asyncio.create_task(state.rate_control(opts))
            await asyncio.sleep(epsilon)  # should be executed immediately
            assert t1.result() is False
            assert t2.result() is False
            assert t3.result() is False
            assert t4.result() is False
            assert t5.result() is True

            t1 = asyncio.create_task(state.rate_control(opts))
            t2 = asyncio.create_task(state.rate_control(opts))
            t3 = asyncio.create_task(state.rate_control(opts))
            t4 = asyncio.create_task(state.rate_control(opts))
            t5 = asyncio.create_task(state.rate_control(opts))
            t6 = asyncio.create_task(state.rate_control(opts))
            await asyncio.sleep(epsilon)
            assert t1.result() is False
            assert t2.result() is False
            assert t3.result() is False
            assert t4.result() is False
            assert t5.result() is True
            assert not t6.done()  # t5 executed but t6 should be pending
            await asyncio.sleep(0.1 + epsilon)
            assert t6.result() is True
