from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogListResult
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import BatchQuerier, Creator

from .db_source import AuditLogDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

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

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AuditLogDBSource(db)

    @audit_log_repository_resilience.apply()
    async def create(self, creator: Creator[AuditLogRow]) -> AuditLogData:
        return await self._db_source.create(creator)

    @audit_log_repository_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> AuditLogListResult:
        """Search audit logs with querier pattern."""
        return await self._db_source.search(querier=querier)
