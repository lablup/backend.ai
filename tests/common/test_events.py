import asyncio
from types import TracebackType
from typing import Type

import aiotools
import attrs
import pytest

from ai.backend.common import config, redis_helper
from ai.backend.common.events import (
    AbstractEvent,
    CoalescingOptions,
    CoalescingState,
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.events_experimental import EventDispatcher as ExperimentalEventDispatcher
from ai.backend.common.types import AgentId, EtcdRedisConfig


@attrs.define(slots=True, frozen=True)
class DummyEvent(AbstractEvent):
    name = "testing"

    value: int = attrs.field()

    def serialize(self) -> tuple:
        return (self.value + 1,)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0] + 1)


EVENT_DISPATCHER_CONSUMER_GROUP = "test"


@pytest.mark.asyncio
@pytest.mark.parametrize("dispatcher_cls", [EventDispatcher, ExperimentalEventDispatcher])
async def test_dispatch(
    dispatcher_cls: type[EventDispatcher] | type[ExperimentalEventDispatcher], redis_container
) -> None:
    app = object()

    redis_config = EtcdRedisConfig(
        addr=redis_container[1], redis_helper_config=config.redis_helper_default_config
    )
    dispatcher = await dispatcher_cls.new(
        redis_config,
        consumer_group=EVENT_DISPATCHER_CONSUMER_GROUP,
    )
    producer = await EventProducer.new(redis_config)

    records = set()

    async def acb(context: object, source: AgentId, event: DummyEvent) -> None:
        assert context is app
        assert source == AgentId("i-test")
        assert isinstance(event, DummyEvent)
        assert event.name == "testing"
        assert event.value == 1001
        await asyncio.sleep(0.01)
        records.add("async")

    def scb(context: object, source: AgentId, event: DummyEvent) -> None:
        assert context is app
        assert source == AgentId("i-test")
        assert isinstance(event, DummyEvent)
        assert event.name == "testing"
        assert event.value == 1001
        records.add("sync")

    dispatcher.subscribe(DummyEvent, app, acb)
    dispatcher.subscribe(DummyEvent, app, scb)
    await asyncio.sleep(0.1)

    # Dispatch the event
    await producer.produce_event(DummyEvent(999), source="i-test")
    await asyncio.sleep(0.2)
    assert records == {"async", "sync"}

    await redis_helper.execute(producer.redis_client, lambda r: r.flushdb())
    await producer.close()
    await dispatcher.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("dispatcher_cls", [EventDispatcher, ExperimentalEventDispatcher])
async def test_error_on_dispatch(
    dispatcher_cls: type[EventDispatcher] | type[ExperimentalEventDispatcher], redis_container
) -> None:
    app = object()
    exception_log: list[str] = []

    async def handle_exception(
        et: Type[Exception],
        exc: Exception,
        tb: TracebackType,
    ) -> None:
        exception_log.append(type(exc).__name__)

    redis_config = EtcdRedisConfig(
        addr=redis_container[1], redis_helper_config=config.redis_helper_default_config
    )
    dispatcher = await dispatcher_cls.new(
        redis_config,
        consumer_group=EVENT_DISPATCHER_CONSUMER_GROUP,
        consumer_exception_handler=handle_exception,
        subscriber_exception_handler=handle_exception,
    )
    producer = await EventProducer.new(redis_config)

    async def acb(context: object, source: AgentId, event: DummyEvent) -> None:
        assert context is app
        assert source == AgentId("i-test")
        assert isinstance(event, DummyEvent)
        raise ZeroDivisionError

    def scb(context: object, source: AgentId, event: DummyEvent) -> None:
        assert context is app
        assert source == AgentId("i-test")
        assert isinstance(event, DummyEvent)
        raise OverflowError

    dispatcher.subscribe(DummyEvent, app, scb)
    dispatcher.subscribe(DummyEvent, app, acb)
    await asyncio.sleep(0.1)

    await producer.produce_event(DummyEvent(0), source="i-test")
    await asyncio.sleep(0.5)
    assert len(exception_log) == 2
    assert "ZeroDivisionError" in exception_log
    assert "OverflowError" in exception_log

    await redis_helper.execute(producer.redis_client, lambda r: r.flushdb())
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
