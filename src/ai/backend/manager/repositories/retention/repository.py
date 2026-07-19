from __future__ import annotations

import logging
from datetime import datetime

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.retention.types import RetentionCategory, RetentionPurgeResult
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.retention.db_source.db_source import RetentionDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RetentionRepository:
    """Deletes accumulated DB records past their category's age boundary.

    A single repository owns the ``category -> tables`` mapping and reuses the
    ``BatchPurger`` framework for chunk-based (delete-and-advance) deletes. The
    leader sweep (separate task) computes ``threshold = now - retention_period``
    per policy and calls :meth:`purge_older_than`.
    """

    _db_source: RetentionDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = RetentionDBSource(ops_provider)

    async def purge_older_than(
        self,
        category: RetentionCategory,
        threshold: datetime,
        batch_size: int,
    ) -> RetentionPurgeResult:
        """Purge rows of ``category`` older than ``threshold``, chunked per table."""
        return await self._db_source.purge_older_than(category, threshold, batch_size)
