"""Database source for scheduling history repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, cast
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.types import KernelId, SessionId
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
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    execute_batch_querier,
    execute_creator,
)
from ai.backend.manager.repositories.scheduling_history.creators import (
    DeploymentHistoryCreatorSpec,
    KernelSchedulingHistoryCreatorSpec,
    RouteHistoryCreatorSpec,
    SessionSchedulingHistoryCreatorSpec,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = ("SchedulingHistoryDBSource",)


class SchedulingHistoryDBSource:
    """Database source for scheduling history operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    # ========== Session History ==========

    async def record_session_history(
        self,
        creator: Creator[SessionSchedulingHistoryRow],
    ) -> SessionSchedulingHistoryData:
        """Record session scheduling history with merge logic."""
        async with self._db.begin_session_read_committed() as db_sess:
            row = await self._record_session_history(db_sess, creator)
            return row.to_data()

    async def _record_session_history(
        self,
        db_sess: SASession,
        creator: Creator[SessionSchedulingHistoryRow],
    ) -> SessionSchedulingHistoryRow:
        spec = cast(SessionSchedulingHistoryCreatorSpec, creator.spec)
        last_row = await self._get_last_session_history(db_sess, spec.session_id)

        if last_row is not None and last_row.should_merge_with(
            spec.phase, spec.result, spec.error_code
        ):
            last_row.attempts += 1
            await db_sess.flush()
            await db_sess.refresh(last_row)
            return last_row

        result = await execute_creator(db_sess, creator)
        return result.row

    async def _get_last_session_history(
        self,
        db_sess: SASession,
        session_id: SessionId,
    ) -> Optional[SessionSchedulingHistoryRow]:
        query = (
            sa.select(SessionSchedulingHistoryRow)
            .where(SessionSchedulingHistoryRow.session_id == session_id)
            .order_by(SessionSchedulingHistoryRow.created_at.desc())
            .limit(1)
        )
        result = await db_sess.execute(query)
        return result.scalar_one_or_none()

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

    async def record_kernel_history(
        self,
        creator: Creator[KernelSchedulingHistoryRow],
    ) -> KernelSchedulingHistoryData:
        """Record kernel scheduling history with merge logic."""
        async with self._db.begin_session_read_committed() as db_sess:
            row = await self._record_kernel_history(db_sess, creator)
            return row.to_data()

    async def _record_kernel_history(
        self,
        db_sess: SASession,
        creator: Creator[KernelSchedulingHistoryRow],
    ) -> KernelSchedulingHistoryRow:
        spec = cast(KernelSchedulingHistoryCreatorSpec, creator.spec)
        last_row = await self._get_last_kernel_history(db_sess, spec.kernel_id)

        if last_row is not None and last_row.should_merge_with(
            spec.phase, spec.result, spec.error_code
        ):
            last_row.attempts += 1
            await db_sess.flush()
            await db_sess.refresh(last_row)
            return last_row

        result = await execute_creator(db_sess, creator)
        return result.row

    async def _get_last_kernel_history(
        self,
        db_sess: SASession,
        kernel_id: KernelId,
    ) -> Optional[KernelSchedulingHistoryRow]:
        query = (
            sa.select(KernelSchedulingHistoryRow)
            .where(KernelSchedulingHistoryRow.kernel_id == kernel_id)
            .order_by(KernelSchedulingHistoryRow.created_at.desc())
            .limit(1)
        )
        result = await db_sess.execute(query)
        return result.scalar_one_or_none()

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

    async def record_deployment_history(
        self,
        creator: Creator[DeploymentHistoryRow],
    ) -> DeploymentHistoryData:
        """Record deployment history with merge logic."""
        async with self._db.begin_session_read_committed() as db_sess:
            row = await self._record_deployment_history(db_sess, creator)
            return row.to_data()

    async def _record_deployment_history(
        self,
        db_sess: SASession,
        creator: Creator[DeploymentHistoryRow],
    ) -> DeploymentHistoryRow:
        spec = cast(DeploymentHistoryCreatorSpec, creator.spec)
        last_row = await self._get_last_deployment_history(db_sess, spec.deployment_id)

        if last_row is not None and last_row.should_merge_with(
            spec.phase, spec.result, spec.error_code
        ):
            last_row.attempts += 1
            await db_sess.flush()
            await db_sess.refresh(last_row)
            return last_row

        result = await execute_creator(db_sess, creator)
        return result.row

    async def _get_last_deployment_history(
        self,
        db_sess: SASession,
        deployment_id: UUID,
    ) -> Optional[DeploymentHistoryRow]:
        query = (
            sa.select(DeploymentHistoryRow)
            .where(DeploymentHistoryRow.deployment_id == deployment_id)
            .order_by(DeploymentHistoryRow.created_at.desc())
            .limit(1)
        )
        result = await db_sess.execute(query)
        return result.scalar_one_or_none()

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

    async def record_route_history(
        self,
        creator: Creator[RouteHistoryRow],
    ) -> RouteHistoryData:
        """Record route history with merge logic."""
        async with self._db.begin_session_read_committed() as db_sess:
            row = await self._record_route_history(db_sess, creator)
            return row.to_data()

    async def _record_route_history(
        self,
        db_sess: SASession,
        creator: Creator[RouteHistoryRow],
    ) -> RouteHistoryRow:
        spec = cast(RouteHistoryCreatorSpec, creator.spec)
        last_row = await self._get_last_route_history(db_sess, spec.route_id)

        if last_row is not None and last_row.should_merge_with(
            spec.phase, spec.result, spec.error_code
        ):
            last_row.attempts += 1
            await db_sess.flush()
            await db_sess.refresh(last_row)
            return last_row

        result = await execute_creator(db_sess, creator)
        return result.row

    async def _get_last_route_history(
        self,
        db_sess: SASession,
        route_id: UUID,
    ) -> Optional[RouteHistoryRow]:
        query = (
            sa.select(RouteHistoryRow)
            .where(RouteHistoryRow.route_id == route_id)
            .order_by(RouteHistoryRow.created_at.desc())
            .limit(1)
        )
        result = await db_sess.execute(query)
        return result.scalar_one_or_none()

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
