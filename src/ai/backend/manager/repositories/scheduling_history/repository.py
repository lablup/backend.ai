from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.policies.retry import BackoffStrategy
from ai.backend.manager.data.deployment.types import (
    DeploymentHistoryListResult,
    RouteHistoryListResult,
)
from ai.backend.manager.data.kernel.types import (
    KernelSchedulingHistoryListResult,
)
from ai.backend.manager.data.session.types import (
    SessionSchedulingHistoryListResult,
)
from ai.backend.manager.repositories.base import BatchQuerier

from .db_source import SchedulingHistoryDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("SchedulingHistoryRepository",)


scheduling_history_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.SCHEDULING_HISTORY_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
            )
        ),
    ]
)


class SchedulingHistoryRepository:
    """Repository for scheduling history data access (read-only)."""

    _db_source: SchedulingHistoryDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = SchedulingHistoryDBSource(db)

    # ========== Session History ==========

    @scheduling_history_repository_resilience.apply()
    async def search_session_history(
        self,
        querier: BatchQuerier,
    ) -> SessionSchedulingHistoryListResult:
        """Search session scheduling history with pagination."""
        return await self._db_source.search_session_history(querier)

    # ========== Kernel History ==========

    @scheduling_history_repository_resilience.apply()
    async def search_kernel_history(
        self,
        querier: BatchQuerier,
    ) -> KernelSchedulingHistoryListResult:
        """Search kernel scheduling history with pagination."""
        return await self._db_source.search_kernel_history(querier)

    # ========== Deployment History ==========

    @scheduling_history_repository_resilience.apply()
    async def search_deployment_history(
        self,
        querier: BatchQuerier,
    ) -> DeploymentHistoryListResult:
        """Search deployment history with pagination."""
        return await self._db_source.search_deployment_history(querier)

    # ========== Route History ==========

    @scheduling_history_repository_resilience.apply()
    async def search_route_history(
        self,
        querier: BatchQuerier,
    ) -> RouteHistoryListResult:
        """Search route history with pagination."""
        return await self._db_source.search_route_history(querier)
