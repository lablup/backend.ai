from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import override
from uuid import uuid4

from ai.backend.common.types import SessionId
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerDefinitionData
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    IdleCheckContext,
    IdleChecker,
    IdleCheckerState,
)
from ai.backend.manager.sokovan.idle_check.handlers.reconcile import IdleCheckReconcileHandler
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckReconcileInfo,
    PreparedChecker,
    PreparedTarget,
)

_NOW = datetime(2026, 1, 2, tzinfo=UTC)


class RecordingState(IdleCheckerState):
    pass


class RecordingChecker(IdleChecker):
    """Judges idle from a preset session-id set and records every check_idle call."""

    _idle_session_ids: frozenset[SessionId]
    checked_session_ids: list[SessionId]

    def __init__(self, idle_session_ids: frozenset[SessionId] = frozenset()) -> None:
        self._idle_session_ids = idle_session_ids
        self.checked_session_ids = []

    @override
    async def prepare(
        self,
        context: IdleCheckContext,
        checker: IdleCheckerDefinitionData,
        sessions: Sequence[IdleCheckSession],
    ) -> IdleCheckerState:
        return RecordingState()

    @override
    def check_idle(self, session_id: SessionId, state: IdleCheckerState) -> bool:
        self.checked_session_ids.append(session_id)
        return session_id in self._idle_session_ids


class TestIdleCheckReconcileHandler:
    async def test_first_idle_verdict_wins_and_short_circuits(self) -> None:
        session_id = SessionId(uuid4())
        first_checker = RecordingChecker(idle_session_ids=frozenset({session_id}))
        second_checker = RecordingChecker(idle_session_ids=frozenset({session_id}))
        reconcile_info = IdleCheckReconcileInfo(
            targets=(
                PreparedTarget(
                    session_id=session_id,
                    checkers=(
                        PreparedChecker(checker=first_checker, state=RecordingState()),
                        PreparedChecker(checker=second_checker, state=RecordingState()),
                    ),
                ),
            ),
            current_time=_NOW,
        )

        result = await IdleCheckReconcileHandler().execute(reconcile_info)

        assert result.idle_session_ids == [session_id]
        assert first_checker.checked_session_ids == [session_id]
        assert second_checker.checked_session_ids == []

    async def test_session_without_idle_verdict_is_not_marked(self) -> None:
        session_id = SessionId(uuid4())
        first_checker = RecordingChecker()
        second_checker = RecordingChecker()
        reconcile_info = IdleCheckReconcileInfo(
            targets=(
                PreparedTarget(
                    session_id=session_id,
                    checkers=(
                        PreparedChecker(checker=first_checker, state=RecordingState()),
                        PreparedChecker(checker=second_checker, state=RecordingState()),
                    ),
                ),
            ),
            current_time=_NOW,
        )

        result = await IdleCheckReconcileHandler().execute(reconcile_info)

        assert result.idle_session_ids == []
        assert first_checker.checked_session_ids == [session_id]
        assert second_checker.checked_session_ids == [session_id]
