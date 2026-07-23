from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import datetime

from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.idle_checker.db_source.db_source import IdleCheckerDBSource
from ai.backend.manager.repositories.idle_checker.types import (
    ExpiredIdleCheckBatchData,
    IdleCheckBatchData,
    InitialGracePeriodBatchData,
    SessionIdleCheckAssignmentData,
    SessionIdleCheckPair,
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

    async def fetch_session_idle_check_assignments(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> SessionIdleCheckAssignmentData:
        return await self._db_source.fetch_session_idle_check_assignments(session_statuses)

    async def fetch_initial_grace_period_checks(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> InitialGracePeriodBatchData:
        return await self._db_source.fetch_initial_grace_period_checks(session_statuses)

    async def fetch_expired_idle_checks(
        self, session_statuses: Collection[SessionStatus]
    ) -> ExpiredIdleCheckBatchData:
        return await self._db_source.fetch_expired_idle_checks(session_statuses)

    async def sync_session_idle_check_assignments(
        self,
        pairs_to_create: Sequence[SessionIdleCheckPair],
        pairs_to_delete: Sequence[SessionIdleCheckPair],
        now: datetime,
    ) -> None:
        await self._db_source.sync_session_idle_check_assignments(
            pairs_to_create,
            pairs_to_delete,
            now,
        )
