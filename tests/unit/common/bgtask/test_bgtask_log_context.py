from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, BackgroundTaskManagerArgs
from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.events.dispatcher import EventProducer


@pytest.fixture
def manager() -> BackgroundTaskManager:
    return BackgroundTaskManager(
        BackgroundTaskManagerArgs(
            event_producer=AsyncMock(spec=EventProducer),
            valkey_client=AsyncMock(spec=ValkeyBgtaskClient),
            server_id="test-server",
        )
    )


async def _wait_for_other_tasks() -> None:
    others = asyncio.all_tasks() - {asyncio.current_task()}
    await asyncio.gather(*others)


async def test_failure_log_carries_task_scope(
    manager: BackgroundTaskManager, caplog: pytest.LogCaptureFixture
) -> None:
    async def failing_task(reporter: ProgressReporter, **kwargs: Any) -> None:
        raise RuntimeError("task failed")

    with caplog.at_level(logging.ERROR, logger="ai.backend.common.bgtask.bgtask"):
        task_id = await manager.start(failing_task, name="failing-task")
        await _wait_for_other_tasks()

    (record,) = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert record.getMessage() == "background task failed"
    assert record.__dict__["log_tag_task_name"] == "failing-task"
    assert record.__dict__["log_tag_bgtask_id"] == str(task_id)
