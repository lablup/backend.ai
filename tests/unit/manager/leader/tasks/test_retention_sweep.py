from __future__ import annotations

from unittest.mock import AsyncMock

from ai.backend.manager.leader.tasks.retention_sweep import RetentionSweepTask


async def test_run_delegates_to_repository_sweep() -> None:
    repo = AsyncMock()
    task = RetentionSweepTask(repository=repo, interval=3600.0)

    await task.run()

    repo.sweep.assert_awaited_once_with()


def test_task_exposes_configured_cadence() -> None:
    repo = AsyncMock()
    task = RetentionSweepTask(repository=repo, interval=1800.0, initial_delay=60.0)

    assert task.name == "retention_sweep"
    assert task.interval == 1800.0
    assert task.initial_delay == 60.0
