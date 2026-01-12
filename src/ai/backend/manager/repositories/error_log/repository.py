from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.error_log.types import ErrorLogData, ErrorLogListResult
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.repositories.base import BatchQuerier, Creator

from .db_source import ErrorLogDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("ErrorLogRepository",)

error_log_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.ERROR_LOG_REPOSITORY)
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


class ErrorLogRepository:
    _db_source: ErrorLogDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ErrorLogDBSource(db)

    @error_log_repository_resilience.apply()
    async def create(self, creator: Creator[ErrorLogRow]) -> ErrorLogData:
        return await self._db_source.create(creator)

    @error_log_repository_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> ErrorLogListResult:
        """Search error logs with querier pattern."""
        return await self._db_source.search(querier=querier)
