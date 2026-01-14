from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.kernel.types import KernelListResult
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    execute_batch_querier,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("KernelDBSource",)

kernel_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.KERNEL_DB_SOURCE)),
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


class KernelDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @kernel_db_source_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> KernelListResult:
        """Search kernels with querier pattern.

        Args:
            querier: BatchQuerier for filtering, ordering, and pagination

        Returns:
            KernelListResult with items, total count, and pagination info
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(KernelRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.KernelRow.to_kernel_info() for row in result.rows]

            return KernelListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
