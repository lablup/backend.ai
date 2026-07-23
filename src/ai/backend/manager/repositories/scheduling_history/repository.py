from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.policies.retry import BackoffStrategy
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.deployment.types import (
    DeploymentHistoryListResult,
    ReplicaGroupHistoryListResult,
    RouteHistoryListResult,
)
from ai.backend.manager.data.kernel.types import (
    KernelSchedulingHistoryListResult,
)
from ai.backend.manager.data.session.types import (
    SessionSchedulingHistoryListResult,
)
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.base import BatchQuerier

from .db_source import SchedulingHistoryDBSource
from .types import (
    DeploymentHistorySearchScope,
    ReplicaGroupHistorySearchScope,
    RouteHistorySearchScope,
    SessionSchedulingHistorySearchScope,
)

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

    # ========== Session History (Admin) ==========

    @scheduling_history_repository_resilience.apply()
    async def search_session_history(
        self,
        querier: BatchQuerier,
    ) -> SessionSchedulingHistoryListResult:
        """Search session scheduling history with pagination (admin API)."""
        return await self._db_source.search_session_history(querier)

    # ========== Session History (Scoped) ==========

    @scheduling_history_repository_resilience.apply()
    async def search_session_scoped_history(
        self,
        querier: BatchQuerier,
        scope: SessionSchedulingHistorySearchScope,
    ) -> SessionSchedulingHistoryListResult:
        """Search session scheduling history within scope."""
        return await self._db_source.search_session_scoped_history(querier, scope)

    # ========== Kernel History (Admin) ==========

    @scheduling_history_repository_resilience.apply()
    async def search_kernel_history(
        self,
        querier: BatchQuerier,
    ) -> KernelSchedulingHistoryListResult:
        """Search kernel scheduling history with pagination."""
        return await self._db_source.search_kernel_history(querier)

    # ========== Kernel History (Scoped) ==========

    @scheduling_history_repository_resilience.apply()
    async def resolve_session_id(self, kernel_id: KernelId) -> SessionId:
        """Return the id of the session owning ``kernel_id``.

        Raises ``KernelNotFound`` when no such kernel exists.
        """
        return await self._db_source.resolve_session_id(kernel_id)

    @scheduling_history_repository_resilience.apply()
    async def search_kernel_scoped_history(
        self,
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> KernelSchedulingHistoryListResult:
        """Search kernel history whose rows match any of ``scopes`` (OR)."""
        return await self._db_source.search_kernel_scoped_history(querier, scopes)

    # ========== Deployment History (Admin) ==========

    @scheduling_history_repository_resilience.apply()
    async def search_deployment_history(
        self,
        querier: BatchQuerier,
    ) -> DeploymentHistoryListResult:
        """Search deployment history with pagination (admin API)."""
        return await self._db_source.search_deployment_history(querier)

    # ========== Deployment History (Scoped) ==========

    @scheduling_history_repository_resilience.apply()
    async def search_deployment_scoped_history(
        self,
        querier: BatchQuerier,
        scope: DeploymentHistorySearchScope,
    ) -> DeploymentHistoryListResult:
        """Search deployment history within scope."""
        return await self._db_source.search_deployment_scoped_history(querier, scope)

    # ========== Replica Group History (Admin) ==========

    @scheduling_history_repository_resilience.apply()
    async def admin_search_replica_group_history(
        self,
        querier: BatchQuerier,
    ) -> ReplicaGroupHistoryListResult:
        """Search replica-group history with pagination (admin API)."""
        return await self._db_source.admin_search_replica_group_history(querier)

    # ========== Replica Group History (Scoped) ==========

    @scheduling_history_repository_resilience.apply()
    async def resolve_replica_group_deployment(
        self, replica_group_id: ReplicaGroupID
    ) -> DeploymentID:
        """Return the id of the deployment owning ``replica_group_id``.

        Raises ``ReplicaGroupNotFound`` when no such replica group exists.
        """
        return await self._db_source.resolve_replica_group_deployment(replica_group_id)

    @scheduling_history_repository_resilience.apply()
    async def search_replica_group_scoped_history(
        self,
        querier: BatchQuerier,
        scope: ReplicaGroupHistorySearchScope,
    ) -> ReplicaGroupHistoryListResult:
        """Search replica-group history within scope."""
        return await self._db_source.search_replica_group_scoped_history(querier, scope)

    # ========== Route History (Admin) ==========

    @scheduling_history_repository_resilience.apply()
    async def search_route_history(
        self,
        querier: BatchQuerier,
    ) -> RouteHistoryListResult:
        """Search route history with pagination (admin API)."""
        return await self._db_source.search_route_history(querier)

    # ========== Route History (Scoped) ==========

    @scheduling_history_repository_resilience.apply()
    async def search_route_scoped_history(
        self,
        querier: BatchQuerier,
        scope: RouteHistorySearchScope,
    ) -> RouteHistoryListResult:
        """Search route history within scope."""
        return await self._db_source.search_route_scoped_history(querier, scope)
