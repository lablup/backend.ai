from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.agent import agents
from ai.backend.manager.models.kernel import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("ManagerAdminDBSource",)

manager_admin_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.MANAGER_ADMIN_DB_SOURCE)
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


class ManagerAdminDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @manager_admin_db_source_resilience.apply()
    async def count_active_sessions(self) -> int:
        """Count the number of currently active sessions."""
        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(sa.func.count())
                .select_from(kernels)
                .where(
                    (kernels.c.cluster_role == DEFAULT_ROLE)
                    & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                )
            )
            result = await db_sess.scalar(query)
            return result or 0

    @manager_admin_db_source_resilience.apply()
    async def update_agent_schedulable(
        self,
        agent_ids: list[str],
        schedulable: bool,
    ) -> int:
        """Update the schedulable flag for the given agents.

        Returns:
            Number of rows updated.
        """
        async with self._db.begin_session() as db_sess:
            query = (
                agents.update().values(schedulable=schedulable).where(agents.c.id.in_(agent_ids))
            )
            result = await db_sess.execute(query)
            return cast(CursorResult[Any], result).rowcount
