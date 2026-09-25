"""Database source for scheduling history repository operations (read-only)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import sqlalchemy as sa

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
from ai.backend.manager.errors.kernel import KernelNotFound
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.replica_group_history.searchers import ReplicaGroupHistorySearcher
from ai.backend.manager.models.scheduling_history.scopes import (
    DeploymentHistoryTarget,
    RouteHistoryTarget,
    SessionSchedulingHistoryTarget,
)
from ai.backend.manager.models.scheduling_history.searchers import (
    DeploymentHistorySearcher,
    KernelSchedulingHistorySearcher,
    RouteHistorySearcher,
    SessionSchedulingHistorySearcher,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = ("SchedulingHistoryDBSource",)


class SchedulingHistoryDBSource:
    """Database source for scheduling history operations (read-only)."""

    _db: ExtendedAsyncSAEngine
    _v2_ops: V2DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, v2_ops: V2DBOpsProvider) -> None:
        self._db = db
        self._v2_ops = v2_ops

    # ========== Session History (Admin) ==========

    async def search_session_scoped_history(
        self,
        searcher: SessionSchedulingHistorySearcher,
        scope: SessionSchedulingHistoryTarget,
    ) -> SessionSchedulingHistoryListResult:
        """Search session scheduling history within scope."""
        async with self._v2_ops.read_ops() as r:
            result = await r.search_with_scopes([scope], searcher)
        return SessionSchedulingHistoryListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # ========== Kernel History (Admin) ==========

    async def resolve_session_id(self, kernel_id: KernelId) -> SessionId:
        """Return the id of the session owning ``kernel_id``.

        Raises ``KernelNotFound`` when no such kernel exists.
        """
        async with self._db.begin_readonly_session() as db_sess:
            session_id = await db_sess.scalar(
                sa.select(KernelRow.session_id).where(KernelRow.id == kernel_id)
            )
            if session_id is None:
                raise KernelNotFound(str(kernel_id))
            return SessionId(session_id)

    async def search_kernel_scoped_history(
        self,
        searcher: KernelSchedulingHistorySearcher,
        scopes: Sequence[OperationScope],
    ) -> KernelSchedulingHistoryListResult:
        """Search kernel history whose rows match any of ``scopes`` (OR)."""
        async with self._v2_ops.read_ops() as r:
            result = await r.search_with_scopes(scopes, searcher)
        return KernelSchedulingHistoryListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # ========== Deployment History (Admin) ==========

    async def search_deployment_scoped_history(
        self,
        searcher: DeploymentHistorySearcher,
        scope: DeploymentHistoryTarget,
    ) -> DeploymentHistoryListResult:
        """Search deployment history within scope."""
        async with self._v2_ops.read_ops() as r:
            result = await r.search_with_scopes([scope], searcher)
        return DeploymentHistoryListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # ========== Replica Group History (Scoped) ==========

    async def scoped_search_replica_group_history(
        self,
        searcher: ReplicaGroupHistorySearcher,
        scopes: Sequence[OperationScope],
    ) -> ReplicaGroupHistoryListResult:
        """Search replica-group history whose rows match any of ``scopes`` (OR)."""
        async with self._v2_ops.read_ops() as r:
            result = await r.search_with_scopes(scopes, searcher)
        return ReplicaGroupHistoryListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # ========== Route History (Scoped) ==========

    async def search_route_scoped_history(
        self,
        searcher: RouteHistorySearcher,
        scope: RouteHistoryTarget,
    ) -> RouteHistoryListResult:
        """Search route history within scope."""
        async with self._v2_ops.read_ops() as r:
            result = await r.search_with_scopes([scope], searcher)
        return RouteHistoryListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
