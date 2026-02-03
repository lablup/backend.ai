"""Database source for scheduling history repository operations (read-only)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

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
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
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

    # ========== Session History ==========

    async def search_session_history(
        self,
        querier: BatchQuerier,
    ) -> SessionSchedulingHistoryListResult:
        """Search session scheduling history with pagination."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(SessionSchedulingHistoryRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.SessionSchedulingHistoryRow.to_data() for row in result.rows]

            return SessionSchedulingHistoryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ========== Kernel History ==========

    async def search_kernel_history(
        self,
        querier: BatchQuerier,
    ) -> KernelSchedulingHistoryListResult:
        """Search kernel scheduling history with pagination."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(KernelSchedulingHistoryRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.KernelSchedulingHistoryRow.to_data() for row in result.rows]

            return KernelSchedulingHistoryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ========== Deployment History ==========

    async def search_deployment_history(
        self,
        querier: BatchQuerier,
    ) -> DeploymentHistoryListResult:
        """Search deployment history with pagination."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(DeploymentHistoryRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.DeploymentHistoryRow.to_data() for row in result.rows]

            return DeploymentHistoryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ========== Route History ==========

    async def search_route_history(
        self,
        querier: BatchQuerier,
    ) -> RouteHistoryListResult:
        """Search route history with pagination."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(RouteHistoryRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.RouteHistoryRow.to_data() for row in result.rows]

            return RouteHistoryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
