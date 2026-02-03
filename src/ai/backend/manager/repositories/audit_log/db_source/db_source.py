from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogListResult
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    execute_batch_querier,
    execute_creator,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("AuditLogDBSource",)

audit_log_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.AUDIT_LOG_DB_SOURCE)),
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


class AuditLogDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @audit_log_db_source_resilience.apply()
    async def create(self, creator: Creator[AuditLogRow]) -> AuditLogData:
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_dataclass()

    @audit_log_db_source_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> AuditLogListResult:
        """Search audit logs with querier pattern.

        Args:
            querier: BatchQuerier for filtering, ordering, and pagination

        Returns:
            AuditLogListResult with items, total count, and pagination info
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AuditLogRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.AuditLogRow.to_dataclass() for row in result.rows]

            return AuditLogListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
