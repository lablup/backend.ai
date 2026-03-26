from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience

from .db_source import EtcdConfigDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("EtcdConfigRepository",)

etcd_config_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.ETCD_CONFIG_REPOSITORY)
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


class EtcdConfigRepository:
    _db_source: EtcdConfigDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = EtcdConfigDBSource(db)

    @etcd_config_repository_resilience.apply()
    async def get_available_agent_slots(self, sgroup: str) -> set[str]:
        """Get available slot keys from agents in the scaling group."""
        return await self._db_source.get_available_agent_slots(sgroup)
