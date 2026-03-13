from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience

from .db_source import ManagerAdminDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("ManagerAdminRepository",)

manager_admin_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.MANAGER_ADMIN_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class ManagerAdminRepository:
    _db_source: ManagerAdminDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ManagerAdminDBSource(db)

    @manager_admin_repository_resilience.apply()
    async def count_active_sessions(self) -> int:
        """Count active sessions."""
        return await self._db_source.count_active_sessions()

    @manager_admin_repository_resilience.apply()
    async def update_agent_schedulable(self, agent_ids: list[str], schedulable: bool) -> int:
        """Update agent schedulable flags. Returns rows updated."""
        return await self._db_source.update_agent_schedulable(agent_ids, schedulable)
