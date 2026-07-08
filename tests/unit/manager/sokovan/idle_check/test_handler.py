from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import override
from uuid import uuid4

import pytest

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleChecker,
    IdleCheckerDependencies,
    IdleCheckerState,
)
from ai.backend.manager.sokovan.idle_check.handlers.reconcile import IdleCheckReconcileHandler
from ai.backend.manager.sokovan.idle_check.types import (
    CheckerWithState,
    IdleCheckReconcileInfo,
    IdleVerdict,
    PreparedTarget,
)

_NOW = datetime(2026, 1, 2, tzinfo=UTC)


class RecordingState(IdleCheckerState):
    pass


class RecordingChecker(IdleChecker[RecordingState]):
    """Judges idle from a preset session-id set and records every check_idle call."""

    _idle_session_ids: frozenset[SessionId]
    checked_session_ids: list[SessionId]

    def __init__(self, idle_session_ids: frozenset[SessionId] = frozenset()) -> None:
        self._idle_session_ids = idle_session_ids
        self.checked_session_ids = []

    @override
    async def prepare(
        self,
        dependencies: IdleCheckerDependencies,
        assignments: Sequence[CheckerAssignment],
    ) -> Mapping[IdleCheckerID, RecordingState]:
        return {assignment.definition.checker_id: RecordingState() for assignment in assignments}

    @override
    def check_idle(self, session_id: SessionId, state: RecordingState) -> bool:
        self.checked_session_ids.append(session_id)
        return session_id in self._idle_session_ids


def _pair(checker: RecordingChecker) -> CheckerWithState:
    return CheckerWithState(
        checker_id=IdleCheckerID(uuid4()), checker=checker, state=RecordingState()
    )


class TestIdleCheckReconcileHandler:
    @pytest.fixture()
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    @pytest.fixture()
    def idle_checker(self, session_id: SessionId) -> RecordingChecker:
        return RecordingChecker(idle_session_ids=frozenset({session_id}))

    @pytest.fixture()
    def second_idle_checker(self, session_id: SessionId) -> RecordingChecker:
        return RecordingChecker(idle_session_ids=frozenset({session_id}))

    @pytest.fixture()
    def active_checker(self) -> RecordingChecker:
        return RecordingChecker()

    @pytest.fixture()
    def second_active_checker(self) -> RecordingChecker:
        return RecordingChecker()

    @pytest.fixture()
    def idle_pair(self, idle_checker: RecordingChecker) -> CheckerWithState:
        return _pair(idle_checker)

    @pytest.fixture()
    def second_idle_pair(self, second_idle_checker: RecordingChecker) -> CheckerWithState:
        return _pair(second_idle_checker)

    @pytest.fixture()
    def active_pair(self, active_checker: RecordingChecker) -> CheckerWithState:
        return _pair(active_checker)

    @pytest.fixture()
    def second_active_pair(self, second_active_checker: RecordingChecker) -> CheckerWithState:
        return _pair(second_active_checker)

    async def test_records_a_verdict_from_every_idle_checker(
        self,
        session_id: SessionId,
        idle_checker: RecordingChecker,
        second_idle_checker: RecordingChecker,
        active_checker: RecordingChecker,
        idle_pair: CheckerWithState,
        second_idle_pair: CheckerWithState,
        active_pair: CheckerWithState,
    ) -> None:
        reconcile_info = IdleCheckReconcileInfo(
            targets=(
                PreparedTarget(
                    session_id=session_id,
                    checkers=(idle_pair, active_pair, second_idle_pair),
                ),
            ),
            current_time=_NOW,
        )

        result = await IdleCheckReconcileHandler().execute(reconcile_info)

        assert result.verdicts == [
            IdleVerdict(
                session_id=session_id,
                checker_ids=[idle_pair.checker_id, second_idle_pair.checker_id],
            ),
        ]
        assert idle_checker.checked_session_ids == [session_id]
        assert active_checker.checked_session_ids == [session_id]
        assert second_idle_checker.checked_session_ids == [session_id]

    async def test_session_without_idle_verdict_is_not_marked(
        self,
        session_id: SessionId,
        active_checker: RecordingChecker,
        second_active_checker: RecordingChecker,
        active_pair: CheckerWithState,
        second_active_pair: CheckerWithState,
    ) -> None:
        reconcile_info = IdleCheckReconcileInfo(
            targets=(
                PreparedTarget(
                    session_id=session_id,
                    checkers=(active_pair, second_active_pair),
                ),
            ),
            current_time=_NOW,
        )

        result = await IdleCheckReconcileHandler().execute(reconcile_info)

        assert result.verdicts == []
        assert active_checker.checked_session_ids == [session_id]
        assert second_active_checker.checked_session_ids == [session_id]
