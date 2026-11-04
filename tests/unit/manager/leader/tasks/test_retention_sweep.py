from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.leader.tasks.retention_sweep import RetentionSweepTask
from ai.backend.manager.repositories.project.types import DanglingPersonalProjectPurgeResult

_NOW = datetime.now(UTC)


def _policy(category: RetentionCategory) -> RetentionPolicyData:
    return RetentionPolicyData(
        id=RetentionPolicyID(uuid4()),
        category=category,
        retention_period=timedelta(days=30),
        enabled=True,
        last_swept_at=None,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _config_provider(batch_size: int = 100) -> MagicMock:
    provider = MagicMock()
    provider.config.retention.batch_size = batch_size
    return provider


async def test_run_sweeps_the_retention_repository() -> None:
    repo = AsyncMock()
    repo.enabled_policy.return_value = None
    task = RetentionSweepTask(
        repository=repo,
        project_repository=AsyncMock(),
        config_provider=_config_provider(),
        interval=3600.0,
    )

    await task.run()

    repo.sweep.assert_awaited_once_with()


async def test_run_purges_dangling_personal_projects_past_the_policy_period() -> None:
    repo = AsyncMock()
    policy = _policy(RetentionCategory.PROJECTS)
    repo.enabled_policy.return_value = policy
    repo.current_time.return_value = now = _NOW
    project_repo = AsyncMock()
    project_repo.purge_dangling_personal_projects.return_value = DanglingPersonalProjectPurgeResult(
        purged_count=2, failed_count=0
    )
    task = RetentionSweepTask(
        repository=repo,
        project_repository=project_repo,
        config_provider=_config_provider(batch_size=5),
        interval=3600.0,
    )

    await task.run()

    repo.enabled_policy.assert_awaited_once_with(RetentionCategory.PROJECTS)
    project_repo.purge_dangling_personal_projects.assert_awaited_once_with(
        now - policy.retention_period, 5
    )
    repo.record_sweep.assert_awaited_once_with(policy.id, now)


async def test_run_skips_projects_when_the_policy_is_disabled() -> None:
    repo = AsyncMock()
    repo.enabled_policy.return_value = None
    project_repo = AsyncMock()
    task = RetentionSweepTask(
        repository=repo,
        project_repository=project_repo,
        config_provider=_config_provider(),
        interval=3600.0,
    )

    await task.run()

    project_repo.purge_dangling_personal_projects.assert_not_awaited()
    repo.record_sweep.assert_not_awaited()


async def test_run_leaves_the_policy_unstamped_when_a_project_purge_fails() -> None:
    repo = AsyncMock()
    repo.enabled_policy.return_value = _policy(RetentionCategory.PROJECTS)
    repo.current_time.return_value = _NOW
    project_repo = AsyncMock()
    project_repo.purge_dangling_personal_projects.return_value = DanglingPersonalProjectPurgeResult(
        purged_count=1, failed_count=1
    )
    task = RetentionSweepTask(
        repository=repo,
        project_repository=project_repo,
        config_provider=_config_provider(),
        interval=3600.0,
    )

    await task.run()

    repo.record_sweep.assert_not_awaited()


async def test_run_leaves_the_policy_unstamped_when_the_purge_raises() -> None:
    repo = AsyncMock()
    repo.enabled_policy.return_value = _policy(RetentionCategory.PROJECTS)
    repo.current_time.return_value = _NOW
    project_repo = AsyncMock()
    project_repo.purge_dangling_personal_projects.side_effect = RuntimeError("boom")
    task = RetentionSweepTask(
        repository=repo,
        project_repository=project_repo,
        config_provider=_config_provider(),
        interval=3600.0,
    )

    await task.run()

    repo.record_sweep.assert_not_awaited()


def test_task_exposes_configured_cadence() -> None:
    task = RetentionSweepTask(
        repository=AsyncMock(),
        project_repository=AsyncMock(),
        config_provider=_config_provider(),
        interval=1800.0,
        initial_delay=60.0,
    )

    assert task.name == "retention_sweep"
    assert task.interval == 1800.0
    assert task.initial_delay == 60.0
