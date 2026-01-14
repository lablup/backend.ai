from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.kernel.types import KernelListResult
from ai.backend.manager.repositories.base import BatchQuerier

from .db_source import KernelDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("KernelRepository",)

kernel_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.KERNEL_REPOSITORY)),
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


class KernelRepository:
    _db_source: KernelDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = KernelDBSource(db)

    @kernel_repository_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> KernelListResult:
        """Search kernels with querier pattern."""
        return await self._db_source.search(querier=querier)
