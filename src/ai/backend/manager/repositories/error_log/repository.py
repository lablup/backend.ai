from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_log.creators import ErrorLogCreator

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
    async def create(self, creator: ErrorLogCreator) -> ErrorLogData:
        """Record an error from an internal path.

        The API records through the action, which runs against ops; this stays for the
        error-monitor plugin, which has no caller identity to audit.
        """
        return await self._db_source.create(creator)

    @error_log_repository_resilience.apply()
    @error_log_repository_resilience.apply()
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
        """List error logs with role-based visibility filtering."""
        return await self._db_source.list_logs(
            user_uuid=user_uuid,
            user_domain=user_domain,
            is_superadmin=is_superadmin,
            is_admin=is_admin,
            page_no=page_no,
            page_size=page_size,
            mark_read=mark_read,
        )
