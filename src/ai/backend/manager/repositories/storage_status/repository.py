from __future__ import annotations

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.repositories.ops.v2.storage_status.provider import StorageStatusOpsProvider
from ai.backend.manager.repositories.ops.v2.storage_status.types import ServiceVolumeStatusReport

__all__ = ("StorageStatusRepository",)

storage_status_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.STORAGE_STATUS_REPOSITORY)
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


class StorageStatusRepository:
    _ops: StorageStatusOpsProvider

    def __init__(self, ops_provider: StorageStatusOpsProvider) -> None:
        self._ops = ops_provider

    @storage_status_repository_resilience.apply()
    async def record_volume_status_report(self, report: ServiceVolumeStatusReport) -> None:
        """Write the volumes one service reported, in one transaction."""
        async with self._ops.write_ops() as w:
            await w.record_volume_status_report(report)
