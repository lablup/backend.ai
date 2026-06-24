from __future__ import annotations

from collections.abc import Collection

from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.idle_checker.db_source.db_source import IdleCheckerDBSource
from ai.backend.manager.repositories.idle_checker.types import IdleCheckSnapshot

__all__ = ("IdleCheckerRepository",)


class IdleCheckerRepository:
    """Reads for the idle-check Source."""

    _db_source: IdleCheckerDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = IdleCheckerDBSource(db)

    async def fetch_idle_check_snapshot(
        self, session_statuses: Collection[SessionStatus]
    ) -> IdleCheckSnapshot:
        return await self._db_source.fetch_idle_check_snapshot(session_statuses)
