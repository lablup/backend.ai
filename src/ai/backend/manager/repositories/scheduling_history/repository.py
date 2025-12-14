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
    DeploymentHistoryData,
    DeploymentHistoryListResult,
    RouteHistoryData,
    RouteHistoryListResult,
)
from ai.backend.manager.data.kernel.types import (
    KernelSchedulingHistoryData,
    KernelSchedulingHistoryListResult,
)
from ai.backend.manager.data.session.types import (
    SessionSchedulingHistoryData,
    SessionSchedulingHistoryListResult,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator

from .db_source import SchedulingHistoryDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.scheduling_history import (
        DeploymentHistoryRow,
        KernelSchedulingHistoryRow,
        RouteHistoryRow,
        SessionSchedulingHistoryRow,
    )
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
    """Repository for scheduling history data access."""

    _db_source: SchedulingHistoryDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = SchedulingHistoryDBSource(db)

    # ========== Session History ==========

    @scheduling_history_repository_resilience.apply()
    async def record_session_history(
        self,
        creator: Creator[SessionSchedulingHistoryRow],
    ) -> SessionSchedulingHistoryData:
        """Record session scheduling history with merge logic."""
        return await self._db_source.record_session_history(creator)

    @scheduling_history_repository_resilience.apply()
    async def search_session_history(
        self,
        querier: BatchQuerier,
    ) -> SessionSchedulingHistoryListResult:
        """Search session scheduling history with pagination."""
        return await self._db_source.search_session_history(querier)

    # ========== Kernel History ==========

    @scheduling_history_repository_resilience.apply()
    async def record_kernel_history(
        self,
        creator: Creator[KernelSchedulingHistoryRow],
    ) -> KernelSchedulingHistoryData:
        """Record kernel scheduling history with merge logic."""
        return await self._db_source.record_kernel_history(creator)

    @scheduling_history_repository_resilience.apply()
    async def search_kernel_history(
        self,
        querier: BatchQuerier,
    ) -> KernelSchedulingHistoryListResult:
        """Search kernel scheduling history with pagination."""
        return await self._db_source.search_kernel_history(querier)

    # ========== Deployment History ==========

    @scheduling_history_repository_resilience.apply()
    async def record_deployment_history(
        self,
        creator: Creator[DeploymentHistoryRow],
    ) -> DeploymentHistoryData:
        """Record deployment history with merge logic."""
        return await self._db_source.record_deployment_history(creator)

    @scheduling_history_repository_resilience.apply()
    async def search_deployment_history(
        self,
        querier: BatchQuerier,
    ) -> DeploymentHistoryListResult:
        """Search deployment history with pagination."""
        return await self._db_source.search_deployment_history(querier)

    # ========== Route History ==========

    @scheduling_history_repository_resilience.apply()
    async def record_route_history(
        self,
        creator: Creator[RouteHistoryRow],
    ) -> RouteHistoryData:
        """Record route history with merge logic."""
        return await self._db_source.record_route_history(creator)

    @scheduling_history_repository_resilience.apply()
    async def search_route_history(
        self,
        querier: BatchQuerier,
    ) -> RouteHistoryListResult:
        """Search route history with pagination."""
        return await self._db_source.search_route_history(querier)
