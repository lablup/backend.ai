from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.models.resource_slot import AgentResourceRow

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("EtcdConfigDBSource",)

etcd_config_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.ETCD_CONFIG_DB_SOURCE)
        ),
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


class EtcdConfigDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @etcd_config_db_source_resilience.apply()
    async def get_available_agent_slots(self, sgroup: str) -> set[str]:
        """Get the set of available slot keys from alive, schedulable agents in a scaling group."""
        async with self._db.begin_readonly_session() as db_sess:
            result = await db_sess.scalars(
                sa.select(AgentResourceRow.slot_name)
                .select_from(
                    sa.join(AgentResourceRow, AgentRow, AgentResourceRow.agent_id == AgentRow.id)
                )
                .where(
                    (AgentRow.status == AgentStatus.ALIVE)
                    & (AgentRow.scaling_group == sgroup)
                    & (AgentRow.schedulable == sa.true())
                )
                .distinct()
            )
            return set(result.all())
