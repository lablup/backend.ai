from __future__ import annotations

from collections.abc import Collection

from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.idle_checker.db_source.db_source import IdleCheckerDBSource
from ai.backend.manager.repositories.idle_checker.types import (
    ExpiredIdleCheckBatchData,
    IdleCheckBatchData,
    SessionIdleCheckPair,
    SessionIdleCheckPairBatchData,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("IdleCheckerRepository",)


class IdleCheckerRepository:
    """Reads for idle-check reconciler Sources."""

    _db_source: IdleCheckerDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = IdleCheckerDBSource(ops_provider)

    async def fetch_judgment_batch(
        self, session_statuses: Collection[SessionStatus]
    ) -> IdleCheckBatchData:
        return await self._db_source.fetch_judgment_batch(session_statuses)

    async def fetch_desired_session_idle_check_pairs(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> list[SessionIdleCheckPair]:
        return await self._db_source.fetch_desired_session_idle_check_pairs(session_statuses)

    async def fetch_current_session_idle_checks(self) -> SessionIdleCheckPairBatchData:
        return await self._db_source.fetch_current_session_idle_checks()

    async def fetch_expired_idle_checks(
        self, session_statuses: Collection[SessionStatus]
    ) -> ExpiredIdleCheckBatchData:
        return await self._db_source.fetch_expired_idle_checks(session_statuses)
