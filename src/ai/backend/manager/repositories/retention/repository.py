from __future__ import annotations

from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.retention.types import RetentionPurgeResult
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.retention.db_source.db_source import RetentionDBSource


class RetentionRepository:
    """Deletes accumulated DB records past their category's age boundary.

    The single caller-facing operation is :meth:`sweep`: it reads every enabled
    ``retention_policies`` row and, per policy, drains records older than
    ``now - retention_period`` and stamps ``last_swept_at`` — one cohesive
    policy-driven action in a single transaction. ``batch_size`` /
    ``per_tick_budget`` are read from config inside the sweep, so it stays
    argument-free and picks up config changes on the next tick.
    """

    _db_source: RetentionDBSource

    def __init__(
        self,
        ops_provider: DBOpsProvider,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db_source = RetentionDBSource(ops_provider, config_provider)

    async def sweep(self) -> list[RetentionPurgeResult]:
        """Sweep every enabled category once against DB-sourced ``now``.

        Returns the per-category purge results (skipped categories excluded).
        """
        return await self._db_source.sweep()
