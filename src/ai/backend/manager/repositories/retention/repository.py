from __future__ import annotations

from datetime import datetime

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.retention.types import RetentionPolicyData, RetentionPurgeResult
from ai.backend.manager.repositories.ops.v2.retention.provider import RetentionOpsProvider
from ai.backend.manager.repositories.retention.db_source.db_source import RetentionDBSource


class RetentionRepository:
    """Deletes accumulated DB records past their category's age boundary.

    :meth:`sweep` reads every enabled ``retention_policies`` row and, per policy,
    drains records older than ``now - retention_period`` and stamps
    ``last_swept_at`` — one cohesive policy-driven action in a single transaction.
    ``batch_size`` / ``per_tick_budget`` are read from config inside the sweep, so
    it stays argument-free and picks up config changes on the next tick.

    A category whose cleanup needs repositories outside this one (``projects``)
    is read and stamped through :meth:`enabled_policy` / :meth:`record_sweep`; the
    leader task owning those dependencies runs it.
    """

    _db_source: RetentionDBSource

    def __init__(
        self,
        ops_provider: RetentionOpsProvider,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db_source = RetentionDBSource(ops_provider, config_provider)

    async def sweep(self) -> list[RetentionPurgeResult]:
        """Sweep every enabled category once against DB-sourced ``now``.

        Returns the per-category purge results (skipped categories excluded).
        """
        return await self._db_source.sweep()

    async def enabled_policy(self, category: RetentionCategory) -> RetentionPolicyData | None:
        """The enabled policy of ``category``, if one is.

        Categories whose cleanup does not run through the drain catalog read their
        policy here and record the run with :meth:`record_sweep`.
        """
        return await self._db_source.enabled_policy(category)

    async def current_time(self) -> datetime:
        """DB-sourced current time, consistent across servers."""
        return await self._db_source.current_time()

    async def record_sweep(self, policy_id: RetentionPolicyID, swept_at: datetime) -> None:
        """Stamp a policy swept by a cleanup outside the drain catalog."""
        await self._db_source.record_sweep(policy_id, swept_at)
