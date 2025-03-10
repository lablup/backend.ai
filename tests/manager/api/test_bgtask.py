from __future__ import annotations

import asyncio
import enum
from collections.abc import AsyncIterator
from typing import Any, TypeAlias

import attr
import pytest

from ai.backend.common.bgtask import BackgroundTaskManager
from ai.backend.common.events import (
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskUpdatedEvent,
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.message_queue.base import MQMessage
from ai.backend.common.types import AgentId
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.server import background_task_ctx, event_dispatcher_ctx, shared_config_ctx


class ContextSentinel(enum.Enum):
    TOKEN = enum.auto()


BgtaskFixture: TypeAlias = tuple[BackgroundTaskManager, EventProducer, EventDispatcher]


@pytest.fixture
async def bgtask_fixture(etcd_fixture, create_app_and_client) -> AsyncIterator[BgtaskFixture]:
    app, client = await create_app_and_client(
        [shared_config_ctx, event_dispatcher_ctx, background_task_ctx],
        [".events"],
    )
    root_ctx: RootContext = app["_root.context"]
    producer: EventProducer = root_ctx.event_producer
    dispatcher: EventDispatcher = root_ctx.event_dispatcher

    yield root_ctx.background_task_manager, producer, dispatcher

    await root_ctx.background_task_manager.shutdown()
    await producer.close()
    await dispatcher.close()
    await producer.message_queue.send(
        MQMessage(
            topic="bgtask",
            payload={},
            metadata={},
        ),
        is_flush=True,
    )


@pytest.mark.timeout(60)
@pytest.mark.asyncio
async def test_background_task(bgtask_fixture: BgtaskFixture) -> None:
    background_task_manager, producer, dispatcher = bgtask_fixture
    update_handler_ctx: dict[str, Any] = {}
    done_handler_ctx: dict[str, Any] = {}

    async def update_sub(
        context: ContextSentinel,
        source: AgentId,
        event: BgtaskUpdatedEvent,
    ) -> None:
        update_handler_ctx["context"] = context
        # Copy the arguments to the uppser scope
        # since assertions inside the handler does not affect the test result
        # because the handlers are executed inside a separate asyncio task.
        update_handler_ctx["event_name"] = event.name
        # type checker complains event is not a subclass of AttrsInstance, but it definitely is...
        update_body = attr.asdict(event)  # type: ignore
        update_handler_ctx.update(**update_body)

    async def done_sub(
        context: ContextSentinel,
        source: AgentId,
        event: BgtaskDoneEvent,
    ) -> None:
        done_handler_ctx["context"] = context
        done_handler_ctx["event_name"] = event.name
        update_body = attr.asdict(event)  # type: ignore
        done_handler_ctx.update(**update_body)

    async def _mock_task(reporter):
        reporter.total_progress = 2
        await asyncio.sleep(1)
        await reporter.update(1, message="BGTask ex1")
        await asyncio.sleep(0.5)
        await reporter.update(1, message="BGTask ex2")
        return "hooray"

    dispatcher.subscribe(BgtaskUpdatedEvent, ContextSentinel.TOKEN, update_sub)
    dispatcher.subscribe(BgtaskDoneEvent, ContextSentinel.TOKEN, done_sub)
    task_id = await background_task_manager.start(_mock_task, name="MockTask1234")
    await asyncio.sleep(2)

    assert update_handler_ctx["context"] is ContextSentinel.TOKEN
    assert update_handler_ctx["task_id"] == task_id
    assert update_handler_ctx["event_name"] == "bgtask_updated"
    assert update_handler_ctx["total_progress"] == 2
    assert update_handler_ctx["message"] in ["BGTask ex1", "BGTask ex2"]
    if update_handler_ctx["message"] == "BGTask ex1":
        assert update_handler_ctx["current_progress"] == 1
    else:
        assert update_handler_ctx["current_progress"] == 2
    assert done_handler_ctx["context"] is ContextSentinel.TOKEN
    assert done_handler_ctx["task_id"] == task_id
    assert done_handler_ctx["event_name"] == "bgtask_done"
    assert done_handler_ctx["message"] == "hooray"


@pytest.mark.timeout(60)
@pytest.mark.asyncio
async def test_background_task_fail(bgtask_fixture: BgtaskFixture) -> None:
    background_task_manager, producer, dispatcher = bgtask_fixture
    fail_handler_ctx: dict[str, Any] = {}

    async def fail_sub(
        context: ContextSentinel,
        source: AgentId,
        event: BgtaskFailedEvent,
    ) -> None:
        fail_handler_ctx["context"] = context
        fail_handler_ctx["event_name"] = event.name
        update_body = attr.asdict(event)  # type: ignore
        fail_handler_ctx.update(**update_body)

    async def _mock_task(reporter):
        reporter.total_progress = 2
        await asyncio.sleep(1)
        await reporter.update(1, message="BGTask ex1")
        raise ZeroDivisionError("oops")

    dispatcher.subscribe(BgtaskFailedEvent, ContextSentinel.TOKEN, fail_sub)
    task_id = await background_task_manager.start(_mock_task, name="MockTask1234")
    await asyncio.sleep(2)

    assert fail_handler_ctx["context"] is ContextSentinel.TOKEN
    assert fail_handler_ctx["task_id"] == task_id
    assert fail_handler_ctx["event_name"] == "bgtask_failed"
    assert fail_handler_ctx["message"] is not None
    assert "ZeroDivisionError" in fail_handler_ctx["message"]
