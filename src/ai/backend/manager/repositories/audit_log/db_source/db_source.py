from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogListResult
from ai.backend.manager.models.audit_log import AuditLogRow, AuditLogScopeRow
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkCreator,
    Creator,
    DependentCreatorSpec,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

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
    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    @audit_log_db_source_resilience.apply()
    async def create(self, creator: Creator[AuditLogRow]) -> AuditLogData:
        async with self._ops.write_ops() as w:
            result = await w.create(creator)
            return result.row.to_dataclass()

    @audit_log_db_source_resilience.apply()
    async def bulk_create_with_scopes(
        self,
        bulk_creator: BulkCreator[AuditLogRow],
        scope_specs: Sequence[DependentCreatorSpec[uuid.UUID, AuditLogScopeRow]],
    ) -> list[AuditLogData]:
        """Insert the audit rows and attach the request's scopes to each, in one transaction."""
        async with self._ops.write_ops() as w:
            result = await w.bulk_create(bulk_creator)
            for row in result.rows:
                if scope_specs:
                    await w.bulk_create_dependent(scope_specs, row.id)
            return [row.to_dataclass() for row in result.rows]

    @audit_log_db_source_resilience.apply()
    async def bulk_create(self, bulk_creator: BulkCreator[AuditLogRow]) -> list[AuditLogData]:
        """Insert multiple audit-log rows in a single bulk operation."""
        async with self._ops.write_ops() as w:
            result = await w.bulk_create(bulk_creator)
            return [row.to_dataclass() for row in result.rows]

    @audit_log_db_source_resilience.apply()
    async def search(self, querier: BatchQuerier) -> AuditLogListResult:
        """Search audit logs across the whole table (super-admin path, no scope filter)."""
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(AuditLogRow), querier)
            return AuditLogListResult(
                items=[row.AuditLogRow.to_dataclass() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    @audit_log_db_source_resilience.apply()
    async def scoped_search(
        self,
        querier: BatchQuerier,
        scopes: Sequence[OperationScope],
    ) -> AuditLogListResult:
        """Search audit logs whose rows match any of ``scopes`` (OR), narrowed by ``querier``."""
        async with self._ops.read_ops() as r:
            result = await r.batch_query_with_scopes(sa.select(AuditLogRow), querier, scopes)
            return AuditLogListResult(
                items=[row.AuditLogRow.to_dataclass() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
