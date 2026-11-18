"""Leader-cron periodic task that sweeps expired DB records (BEP-1063).

Registered as a single :class:`PeriodicTask` on the manager's ``LeaderCron`` so
it runs only on the leader (leader election guarantees a single executor — no
``GlobalTimer`` or distributed lock). Each tick delegates the whole policy-driven
sweep to :meth:`RetentionRepository.sweep`; this task only owns the cadence.

``projects`` is not drained as plain rows: a personal project carries sessions,
kernels, deployments and vfolders, which only the project repository with its
storage manager can clear. The task reads that policy and runs it here.
"""

from __future__ import annotations

import logging
from typing import Final, override

from ai.backend.common.cron.base import PeriodicTask
from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.retention.types import RetentionPurgeResult
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.retention.repository import RetentionRepository

log = StructuredLogger(logging.getLogger(__spec__.name))


class RetentionSweepTask(PeriodicTask):
    """Periodically purges DB records past each enabled policy's age boundary."""

    _repository: Final[RetentionRepository]
    _project_repository: Final[ProjectRepository]
    _config_provider: Final[ManagerConfigProvider]
    _interval: Final[float]
    _initial_delay: Final[float]

    def __init__(
        self,
        repository: RetentionRepository,
        project_repository: ProjectRepository,
        config_provider: ManagerConfigProvider,
        interval: float,
        initial_delay: float = 0.0,
    ) -> None:
        self._repository = repository
        self._project_repository = project_repository
        self._config_provider = config_provider
        self._interval = interval
        self._initial_delay = initial_delay

    @override
    async def run(self) -> None:
        """Run one sweep. All orchestration lives in the repositories."""
        results = await self._repository.sweep()
        await self._sweep_dangling_personal_projects(results)

    async def _sweep_dangling_personal_projects(self, drained: list[RetentionPurgeResult]) -> None:
        """Purge personal projects whose creator is gone, after the policy period."""
        budget = self._config_provider.config.retention.per_tick_budget
        if budget is not None and sum(result.deleted_count for result in drained) >= budget:
            log.debug("retention sweep per-tick budget exhausted, projects deferred")
            return
        try:
            policy = await self._repository.enabled_policy(RetentionCategory.PROJECTS)
            if policy is None:
                return
            now = await self._repository.current_time()
            threshold = now - policy.retention_period
            result = await self._project_repository.purge_dangling_personal_projects(
                threshold,
                self._config_provider.config.retention.batch_size,
            )
            if result.failed_count:
                log.warning(
                    "dangling personal project purge incomplete",
                    failed_count=result.failed_count,
                )
                return
            await self._repository.record_sweep(policy.id, now)
        except Exception:
            log.exception(
                "retention sweep failed for category, skipped",
                retention_category=RetentionCategory.PROJECTS,
            )
            return
        if result.purged_count:
            log.info("dangling personal projects purged", purged_count=result.purged_count)
        else:
            log.debug("dangling personal projects sweep found none")

    @property
    @override
    def name(self) -> str:
        return "retention_sweep"

    @property
    @override
    def interval(self) -> float:
        return self._interval

    @property
    @override
    def initial_delay(self) -> float:
        return self._initial_delay
