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
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.replica_group_history.searchable_fields import (
    ReplicaGroupHistorySearchableFields,
)
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.scheduling_history.scopes import (
    DeploymentHistoryTarget,
    RouteHistoryTarget,
    SessionSchedulingHistoryTarget,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    execute_batch_querier,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = ("SchedulingHistoryDBSource",)


class SchedulingHistoryDBSource:
    """Database source for scheduling history operations (read-only)."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    # ========== Session History (Admin) ==========

    async def search_session_scoped_history(
        self,
        querier: BatchQuerier,
        scope: SessionSchedulingHistoryTarget,
    ) -> SessionSchedulingHistoryListResult:
        """Search session scheduling history within scope."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(SessionSchedulingHistoryRow)

            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])

            items = [row.SessionSchedulingHistoryRow.to_data() for row in result.rows]

            return SessionSchedulingHistoryListResult(
                items=items,
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
        querier: BatchQuerier,
        scopes: Sequence[OperationScope],
    ) -> KernelSchedulingHistoryListResult:
        """Search kernel history whose rows match any of ``scopes`` (OR), narrowed by ``querier``."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(KernelSchedulingHistoryRow)

            result = await execute_batch_querier(db_sess, query, querier, scopes=scopes)

            items = [row.KernelSchedulingHistoryRow.to_data() for row in result.rows]

            return KernelSchedulingHistoryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ========== Deployment History (Admin) ==========

    async def search_deployment_scoped_history(
        self,
        querier: BatchQuerier,
        scope: DeploymentHistoryTarget,
    ) -> DeploymentHistoryListResult:
        """Search deployment history within scope."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(DeploymentHistoryRow)

            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])

            items = [row.DeploymentHistoryRow.to_data() for row in result.rows]

            return DeploymentHistoryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ========== Replica Group History (Scoped) ==========

    async def scoped_search_replica_group_history(
        self,
        querier: BatchQuerier,
        scopes: Sequence[OperationScope],
    ) -> ReplicaGroupHistoryListResult:
        """Search replica-group history whose rows match any of ``scopes`` (OR), narrowed by ``querier``."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ReplicaGroupHistoryRow)

            result = await execute_batch_querier(db_sess, query, querier, scopes=scopes)

            items = [
                ReplicaGroupHistorySearchableFields.own.to_data(row.ReplicaGroupHistoryRow)
                for row in result.rows
            ]

            return ReplicaGroupHistoryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ========== Route History (Admin) ==========

    async def search_route_scoped_history(
        self,
        querier: BatchQuerier,
        scope: RouteHistoryTarget,
    ) -> RouteHistoryListResult:
        """Search route history within scope."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(RouteHistoryRow)

            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])

            items = [row.RouteHistoryRow.to_data() for row in result.rows]

            return RouteHistoryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
