from __future__ import annotations

import asyncio
import enum
from collections.abc import AsyncIterator
from dataclasses import asdict
from typing import Any, TypeAlias

import pytest

from ai.backend.common import redis_helper
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.events.event_types.bgtask.broadcast import (
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskUpdatedEvent,
)
from ai.backend.common.types import AgentId
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.server import (
    agent_registry_ctx,
    background_task_ctx,
    database_ctx,
    event_dispatcher_plugin_ctx,
    event_hub_ctx,
    event_producer_ctx,
    hook_plugin_ctx,
    message_queue_ctx,
    monitoring_ctx,
    network_plugin_ctx,
    redis_ctx,
    repositories_ctx,
    storage_manager_ctx,
)


class ContextSentinel(enum.Enum):
    TOKEN = enum.auto()


BgtaskFixture: TypeAlias = tuple[BackgroundTaskManager, EventProducer, EventDispatcher]


@pytest.fixture
async def bgtask_fixture(
    etcd_fixture,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    event_dispatcher_test_ctx,
    database_fixture,
    create_app_and_client,
) -> AsyncIterator[BgtaskFixture]:
    app, client = await create_app_and_client(
        [
            event_hub_ctx,
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            redis_ctx,
            message_queue_ctx,
            event_producer_ctx,
            storage_manager_ctx,
            repositories_ctx,
            monitoring_ctx,
            network_plugin_ctx,
            hook_plugin_ctx,
            event_dispatcher_plugin_ctx,
            agent_registry_ctx,
            event_dispatcher_test_ctx,
            background_task_ctx,
        ],
        [".events"],
    )
    root_ctx: RootContext = app["_root.context"]
    producer: EventProducer = root_ctx.event_producer
    dispatcher: EventDispatcher = root_ctx.event_dispatcher

    yield root_ctx.background_task_manager, producer, dispatcher

    etcd_redis_config = root_ctx.config_provider.config.redis.to_redis_profile_target()
    stream_redis_config = etcd_redis_config.profile_target(RedisRole.STREAM)
    stream_redis = redis_helper.get_redis_object(
        stream_redis_config,
        name="event_producer.stream",
        db=REDIS_STREAM_DB,
    )

    await root_ctx.background_task_manager.shutdown()
    await producer.close()
    await dispatcher.close()
    await redis_helper.execute(stream_redis, lambda r: r.flushdb())


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
        fail_handler_ctx["event_name"] = event.event_name()
        update_body = asdict(event)
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
