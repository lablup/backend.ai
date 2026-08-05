from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogListResult
from ai.backend.manager.models.audit_log import AuditLogRow, AuditLogScopeRow
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkCreator,
    Creator,
    DependentCreatorSpec,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

from .db_source import AuditLogDBSource

__all__ = ("AuditLogRepository",)

audit_log_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.AUDIT_LOG_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class AuditLogRepository:
    _db_source: AuditLogDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = AuditLogDBSource(ops_provider)

    @audit_log_repository_resilience.apply()
    async def create(self, creator: Creator[AuditLogRow]) -> AuditLogData:
        return await self._db_source.create(creator)

    @audit_log_repository_resilience.apply()
    async def bulk_create_with_scopes(
        self,
        bulk_creator: BulkCreator[AuditLogRow],
        scope_specs: Sequence[DependentCreatorSpec[uuid.UUID, AuditLogScopeRow]],
    ) -> list[AuditLogData]:
        """Create audit rows and attach the request's scopes to each, in one transaction."""
        return await self._db_source.bulk_create_with_scopes(bulk_creator, scope_specs)

    @audit_log_repository_resilience.apply()
    async def bulk_create(self, bulk_creator: BulkCreator[AuditLogRow]) -> list[AuditLogData]:
        """Insert multiple audit-log rows in a single bulk operation."""
        return await self._db_source.bulk_create(bulk_creator)

    @audit_log_repository_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> AuditLogListResult:
        """Search audit logs with querier pattern."""
        return await self._db_source.search(querier=querier)

    @audit_log_repository_resilience.apply()
    async def scoped_search(
        self,
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> AuditLogListResult:
        """Search audit logs whose rows match any of ``scopes`` (OR), narrowed by ``querier``."""
        return await self._db_source.scoped_search(querier=querier, scopes=scopes)
