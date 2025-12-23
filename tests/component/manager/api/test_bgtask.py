from __future__ import annotations

import asyncio
import enum
from collections.abc import AsyncIterator
from dataclasses import asdict
from typing import Any
from uuid import uuid4

import pytest

from ai.backend.common import redis_helper
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.defs import REDIS_BGTASK_DB, REDIS_STREAM_DB
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.events.event_types.bgtask.broadcast import (
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskUpdatedEvent,
)
from ai.backend.common.message_queue.redis_queue.queue import RedisMQArgs, RedisQueue
from ai.backend.common.types import AgentId, RedisTarget, ValkeyTarget


class ContextSentinel(enum.Enum):
    TOKEN = enum.auto()


@pytest.fixture
async def message_queue(
    redis_container,
) -> AsyncIterator[RedisQueue]:
    _, redis_addr = redis_container
    redis_target = RedisTarget(addr=redis_addr, redis_helper_config={})
    message_queue = await RedisQueue.create(
        redis_target,
        RedisMQArgs(
            anycast_stream_key="events",
            broadcast_channel="events_all",
            consume_stream_keys={"events"},
            subscribe_channels={"events_all"},
            group_name=f"test_message_queue_group_{uuid4()}",
            node_id=f"test_node_{uuid4()}",
            db=REDIS_STREAM_DB,
        ),
    )

    yield message_queue

    await message_queue.close()
    stream_redis_conn = redis_helper.get_redis_object(
        redis_target,
        name="test_cleanup_stream",
        db=REDIS_STREAM_DB,
    )
    try:
        await redis_helper.execute(stream_redis_conn, lambda r: r.flushdb())
    finally:
        await stream_redis_conn.close()


@pytest.fixture
async def event_producer(
    message_queue: RedisQueue,
) -> AsyncIterator[EventProducer]:
    producer = EventProducer(
        message_queue,
        source=AgentId(f"test-agent-{uuid4()}"),
    )
    try:
        yield producer

    finally:
        await producer.close()


@pytest.fixture
async def event_dispatcher(
    message_queue: RedisQueue,
) -> AsyncIterator[EventDispatcher]:
    dispatcher = EventDispatcher(message_queue)
    try:
        await dispatcher.start()
        yield dispatcher
    finally:
        await dispatcher.close()


@pytest.fixture
async def valkey_bgtask_client(
    redis_container,
) -> AsyncIterator[ValkeyBgtaskClient]:
    _, redis_addr = redis_container
    redis_target = RedisTarget(addr=redis_addr, redis_helper_config={})

    valkey_target = ValkeyTarget(
        addr=redis_addr.address,
    )

    valkey_client = await ValkeyBgtaskClient.create(
        valkey_target,
        db_id=REDIS_BGTASK_DB,
        human_readable_name=f"test_bgtask_client_{uuid4()}",
    )

    yield valkey_client

    await valkey_client.close()

    # Flush BGTASK_DB for test isolation
    bgtask_redis_conn = redis_helper.get_redis_object(
        redis_target,
        name="test_cleanup_bgtask",
        db=REDIS_BGTASK_DB,
    )
    try:
        await redis_helper.execute(bgtask_redis_conn, lambda r: r.flushdb())
    finally:
        await bgtask_redis_conn.close()


@pytest.fixture
async def background_task_manager(
    event_producer: EventProducer,
    valkey_bgtask_client: ValkeyBgtaskClient,
) -> AsyncIterator[BackgroundTaskManager]:
    bgtask_manager = BackgroundTaskManager(
        event_producer,
        valkey_client=valkey_bgtask_client,
        server_id=f"test-server-{uuid4()}",
    )

    yield bgtask_manager

    await bgtask_manager.shutdown()


@pytest.mark.timeout(60)
@pytest.mark.asyncio
async def test_background_task(
    background_task_manager: BackgroundTaskManager,
    event_dispatcher: EventDispatcher,
) -> None:
    update_handler_ctx: dict[str, Any] = {}
    done_handler_ctx: dict[str, Any] = {}
    update_call_count = 0

    async def update_sub(
        context: ContextSentinel,
        source: AgentId,
        event: BgtaskUpdatedEvent,
    ) -> None:
        nonlocal update_call_count
        update_call_count += 1
        update_handler_ctx["context"] = context
        # Copy the arguments to the uppser scope
        # since assertions inside the handler does not affect the test result
        # because the handlers are executed inside a separate asyncio task.
        update_handler_ctx["event_name"] = event.event_name()
        # type checker complains event is not a subclass of AttrsInstance, but it definitely is...
        update_body = asdict(event)
        update_handler_ctx.update(**update_body)

    async def done_sub(
        context: ContextSentinel,
        source: AgentId,
        event: BgtaskDoneEvent,
    ) -> None:
        done_handler_ctx["context"] = context
        done_handler_ctx["event_name"] = event.event_name()
        update_body = asdict(event)
        done_handler_ctx.update(**update_body)

    async def _mock_task(reporter):
        reporter.total_progress = 2
        await asyncio.sleep(0.1)
        await reporter.update(1, message="BGTask ex1")
        await asyncio.sleep(0.1)
        await reporter.update(1, message="BGTask ex2")
        return "hooray"

    event_dispatcher.subscribe(BgtaskUpdatedEvent, ContextSentinel.TOKEN, update_sub)
    event_dispatcher.subscribe(BgtaskDoneEvent, ContextSentinel.TOKEN, done_sub)
    task_id = await background_task_manager.start(_mock_task, name="MockTask1234")

    # Wait for task completion and event processing
    await asyncio.sleep(1.0)

    # Wait a bit more for event handlers to be called
    for _ in range(50):  # Max 5 seconds
        if "context" in done_handler_ctx:
            break
        await asyncio.sleep(0.1)

    assert "context" in update_handler_ctx, "update_sub handler was not called"
    assert update_handler_ctx["context"] is ContextSentinel.TOKEN
    assert update_handler_ctx["task_id"] == task_id
    assert update_handler_ctx["event_name"] == "bgtask_updated"
    assert update_handler_ctx["total_progress"] == 2
    assert update_handler_ctx["message"] in ["BGTask ex1", "BGTask ex2", "Task started"]
    if update_handler_ctx["message"] == "BGTask ex1":
        assert update_handler_ctx["current_progress"] == 1
    elif update_handler_ctx["message"] == "BGTask ex2":
        assert update_handler_ctx["current_progress"] == 2
    # "Task started" message has current_progress == 0

    assert "context" in done_handler_ctx, "done_sub handler was not called"
    assert done_handler_ctx["context"] is ContextSentinel.TOKEN
    assert done_handler_ctx["task_id"] == task_id
    assert done_handler_ctx["event_name"] == "bgtask_done"
    assert done_handler_ctx["message"] == "hooray"


@pytest.mark.timeout(60)
@pytest.mark.asyncio
async def test_background_task_fail(
    background_task_manager: BackgroundTaskManager, event_dispatcher: EventDispatcher
) -> None:
    fail_handler_ctx: dict[str, Any] = {}

    async def fail_sub(
        context: ContextSentinel,
        source: AgentId,
        event: BgtaskFailedEvent,
    ) -> None:
        fail_handler_ctx["context"] = context
        fail_handler_ctx["event_name"] = event.event_name()
        update_body = asdict(event)
        fail_handler_ctx.update(**update_body)

    async def _mock_task(reporter):
        reporter.total_progress = 2
        await asyncio.sleep(0.1)
        await reporter.update(1, message="BGTask ex1")
        raise ZeroDivisionError("oops")

    event_dispatcher.subscribe(BgtaskFailedEvent, ContextSentinel.TOKEN, fail_sub)
    task_id = await background_task_manager.start(_mock_task, name="MockTask1234")

    # Wait for task completion and event processing
    await asyncio.sleep(1.0)

    # Wait a bit more for event handlers to be called
    for _ in range(50):  # Max 5 seconds
        if "context" in fail_handler_ctx:
            break
        await asyncio.sleep(0.1)

    assert "context" in fail_handler_ctx, "fail_sub handler was not called"
    assert fail_handler_ctx["context"] is ContextSentinel.TOKEN
    assert fail_handler_ctx["task_id"] == task_id
    assert fail_handler_ctx["event_name"] == "bgtask_failed"
    assert fail_handler_ctx["message"] is not None
    assert "ZeroDivisionError" in fail_handler_ctx["message"]
