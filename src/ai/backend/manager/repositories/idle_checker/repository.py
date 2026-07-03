from __future__ import annotations

from collections.abc import Collection

from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.idle_checker.db_source.db_source import IdleCheckerDBSource
from ai.backend.manager.repositories.idle_checker.types import IdleCheckBatchData
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("IdleCheckerRepository",)


class IdleCheckerRepository:
    """Reads for the idle-check Source."""

    _db_source: IdleCheckerDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = IdleCheckerDBSource(ops_provider)

    async def fetch_idle_check_batch(
        self, session_statuses: Collection[SessionStatus]
    ) -> IdleCheckBatchData:
        return await self._db_source.fetch_idle_check_batch(session_statuses)
