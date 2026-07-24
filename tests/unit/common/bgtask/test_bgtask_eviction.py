"""Regression tests for BA-6803.

Retriable background tasks were only popped from ``_ongoing_tasks`` on the legacy
``start()`` path, so completed ``start_retriable()`` tasks lingered forever and kept
being re-registered to Valkey by ``do_heartbeat()``. These tests verify a completed
retriable task is evicted and no longer heartbeated.
"""

from __future__ import annotations

import asyncio
import enum
from typing import cast, override
from unittest.mock import AsyncMock

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, BackgroundTaskManagerArgs
from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskManifest,
)
from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry
from ai.backend.common.bgtask.types import BgtaskNameBase, TaskID
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.events.dispatcher import EventProducer


class _RegressionTaskName(enum.StrEnum):
    NOOP = "regression_noop_task"

    @classmethod
    def from_str(cls, value: str) -> _RegressionTaskName:
        return cls(value)


class _NoopManifest(BaseBackgroundTaskManifest):
    pass


class _NoopHandler(BaseBackgroundTaskHandler[_NoopManifest, None]):
    @classmethod
    @override
    def name(cls) -> BgtaskNameBase:
        return _RegressionTaskName.NOOP

    @classmethod
    @override
    def manifest_type(cls) -> type[_NoopManifest]:
        return _NoopManifest

    @override
    async def execute(self, manifest: _NoopManifest) -> None:
        return None


def _make_manager() -> tuple[BackgroundTaskManager, AsyncMock]:
    valkey = AsyncMock()
    manager = BackgroundTaskManager(
        BackgroundTaskManagerArgs(
            event_producer=cast(EventProducer, AsyncMock()),
            valkey_client=cast(ValkeyBgtaskClient, valkey),
            server_id="regression-server",
        )
    )
    registry = BackgroundTaskHandlerRegistry()
    registry.register(_NoopHandler())
    manager.set_registry(registry)
    return manager, valkey


async def _wait_until_evicted(manager: BackgroundTaskManager, task_id: TaskID) -> None:
    for _ in range(200):
        if task_id not in manager._ongoing_tasks:
            return
        await asyncio.sleep(0.02)


class TestRetriableTaskEviction:
    async def test_completed_retriable_task_is_removed_from_ongoing_tasks(self) -> None:
        manager, _ = _make_manager()
        task_id = await manager.start_retriable(_RegressionTaskName.NOOP, _NoopManifest())
        await _wait_until_evicted(manager, task_id)
        assert task_id not in manager._ongoing_tasks
        assert manager._ongoing_tasks == {}

    async def test_heartbeat_does_not_reregister_completed_task(self) -> None:
        manager, valkey = _make_manager()
        task_id = await manager.start_retriable(_RegressionTaskName.NOOP, _NoopManifest())
        await _wait_until_evicted(manager, task_id)
        await manager.do_heartbeat()
        alive_task_info = valkey.heartbeat.call_args.args[0]
        assert alive_task_info == []
