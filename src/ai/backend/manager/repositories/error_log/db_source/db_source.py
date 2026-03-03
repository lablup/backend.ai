from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.error_log.types import ErrorLogData, ErrorLogListResult
from ai.backend.manager.models.error_logs import ErrorLogRow, error_logs
from ai.backend.manager.models.group.row import AssocGroupUserRow, GroupRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    execute_batch_querier,
    execute_creator,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("ErrorLogDBSource",)

error_log_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.ERROR_LOG_DB_SOURCE)),
        RetryPolicy(
            RetryArgs(
                max_retries=5,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class ErrorLogDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @error_log_db_source_resilience.apply()
    async def create(self, creator: Creator[ErrorLogRow]) -> ErrorLogData:
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_dataclass()

    @error_log_db_source_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> ErrorLogListResult:
        """Search error logs with querier pattern.

        Args:
            querier: BatchQuerier for filtering, ordering, and pagination

        Returns:
            ErrorLogListResult with items, total count, and pagination info
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ErrorLogRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.ErrorLogRow.to_dataclass() for row in result.rows]

            return ErrorLogListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    @error_log_db_source_resilience.apply()
    async def list_logs(
        self,
        *,
        user_uuid: uuid.UUID,
        user_domain: str,
        is_superadmin: bool,
        is_admin: bool,
        page_no: int,
        page_size: int,
        mark_read: bool,
    ) -> tuple[list[ErrorLogData], int]:
        """List error logs with role-based visibility filtering.

        Returns:
            Tuple of (log items, total count).
        """
        async with self._db.begin_session() as db_sess:
            select_query = (
                sa.select(ErrorLogRow).order_by(sa.desc(error_logs.c.created_at)).limit(page_size)
            )
            count_query = sa.select(sa.func.count()).select_from(error_logs)
            if page_no > 1:
                select_query = select_query.offset((page_no - 1) * page_size)

            if is_superadmin:
                pass
            elif is_admin:
                j = sa.join(
                    GroupRow.__table__,
                    AssocGroupUserRow.__table__,
                    GroupRow.id == AssocGroupUserRow.group_id,
                )
                usr_query = (
                    sa.select(AssocGroupUserRow.user_id)
                    .select_from(j)
                    .where(GroupRow.domain_name == user_domain)
                )
                usr_result = await db_sess.execute(usr_query)
                user_ids = [row.user_id for row in usr_result]
                where = error_logs.c.user.in_(user_ids)
                select_query = select_query.where(where)
                count_query = count_query.where(where)
            else:
                user_where = (error_logs.c.user == user_uuid) & (~error_logs.c.is_cleared)
                select_query = select_query.where(user_where)
                count_query = count_query.where(user_where)

            logs_result = await db_sess.execute(select_query)
            items = [row.to_dataclass() for row in logs_result.scalars()]
            total_count_val = await db_sess.scalar(count_query)
            total_count = total_count_val or 0

            if mark_read and items:
                read_update_query = (
                    sa.update(error_logs)
                    .values(is_read=True)
                    .where(error_logs.c.id.in_([item.id for item in items]))
                )
                await db_sess.execute(read_update_query)

            return items, total_count

    @error_log_db_source_resilience.apply()
    async def mark_cleared(
        self,
        *,
        log_id: uuid.UUID,
        user_uuid: uuid.UUID,
        user_domain: str,
        is_superadmin: bool,
        is_admin: bool,
    ) -> int:
        """Mark an error log as cleared with role-based authorization.

        Returns:
            Number of rows updated (expected 1 on success).
        """
        async with self._db.begin_session() as db_sess:
            update_query = sa.update(error_logs).values(is_cleared=True)

            if is_superadmin:
                update_query = update_query.where(error_logs.c.id == log_id)
            elif is_admin:
                j = sa.join(
                    GroupRow.__table__,
                    AssocGroupUserRow.__table__,
                    GroupRow.id == AssocGroupUserRow.group_id,
                )
                usr_query = (
                    sa.select(AssocGroupUserRow.user_id)
                    .select_from(j)
                    .where(GroupRow.domain_name == user_domain)
                )
                usr_result = await db_sess.execute(usr_query)
                user_ids = [row.user_id for row in usr_result]
                update_query = update_query.where(
                    (error_logs.c.user.in_(user_ids)) & (error_logs.c.id == log_id),
                )
            else:
                update_query = update_query.where(
                    (error_logs.c.user == user_uuid) & (error_logs.c.id == log_id),
                )

            update_result = await db_sess.execute(update_query)
            return cast(CursorResult[Any], update_result).rowcount
