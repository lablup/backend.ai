from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.idle_checker.types import (
    SessionIdleCheckAssignmentData,
    SessionIdleCheckPair,
)
from ai.backend.manager.sokovan.idle_check.assignment_sync.source import (
    IdleCheckAssignmentSyncSource,
)
from ai.backend.manager.sokovan.idle_check.source import IdleCheckSource
from ai.backend.manager.sokovan.idle_check.types import IdleCheckCategory, IdleCheckTargetStatuses


@dataclass(frozen=True)
class AssignmentSyncSourceCase:
    source: IdleCheckAssignmentSyncSource
    repository: MagicMock
    target_statuses: IdleCheckTargetStatuses
    session_id: SessionId
    first_checker_id: IdleCheckerID
    second_checker_id: IdleCheckerID
    existing_pair: SessionIdleCheckPair
    now: datetime


class TestIdleCheckSource:
    async def test_returns_fetched_batch_with_current_time(self) -> None:
        batch = MagicMock()
        repository = MagicMock()
        repository.fetch_judgment_batch = AsyncMock(return_value=batch)
        target_statuses = IdleCheckTargetStatuses(
            session_statuses=frozenset([SessionStatus.RUNNING])
        )

        reconcile_info = await IdleCheckSource(repository).fetch_reconcile_info(
            IdleCheckCategory.IDLE, target_statuses
        )

        assert reconcile_info.batch is batch
        repository.fetch_judgment_batch.assert_awaited_once_with(target_statuses.session_statuses)
        assert reconcile_info.current_time.tzinfo == UTC


class TestIdleCheckAssignmentSyncSource:
    @pytest.fixture
    def assignment_sync_source_case(self) -> AssignmentSyncSourceCase:
        session_id = SessionId(uuid4())
        first_checker_id = IdleCheckerID(uuid4())
        second_checker_id = IdleCheckerID(uuid4())
        existing_pair = SessionIdleCheckPair(SessionId(uuid4()), IdleCheckerID(uuid4()))
        desired_pairs = [
            SessionIdleCheckPair(session_id, first_checker_id),
            SessionIdleCheckPair(session_id, second_checker_id),
        ]
        now = datetime(2026, 7, 22, tzinfo=UTC)
        assignments = SessionIdleCheckAssignmentData(
            desired_pairs=desired_pairs,
            current_pairs=(existing_pair,),
            now=now,
        )
        repository = MagicMock()
        repository.fetch_session_idle_check_assignments = AsyncMock(return_value=assignments)
        target_statuses = IdleCheckTargetStatuses(
            session_statuses=frozenset({SessionStatus.RUNNING})
        )
        return AssignmentSyncSourceCase(
            source=IdleCheckAssignmentSyncSource(repository),
            repository=repository,
            target_statuses=target_statuses,
            session_id=session_id,
            first_checker_id=first_checker_id,
            second_checker_id=second_checker_id,
            existing_pair=existing_pair,
            now=now,
        )

    async def test_returns_desired_and_current_pairs(
        self,
        assignment_sync_source_case: AssignmentSyncSourceCase,
    ) -> None:
        case = assignment_sync_source_case

        reconcile_info = await case.source.fetch_reconcile_info(
            IdleCheckCategory.IDLE,
            case.target_statuses,
        )

        assert reconcile_info.desired_pairs == [
            SessionIdleCheckPair(case.session_id, case.first_checker_id),
            SessionIdleCheckPair(case.session_id, case.second_checker_id),
        ]
        assert reconcile_info.current_pairs == (case.existing_pair,)
        assert reconcile_info.now() == case.now
        case.repository.fetch_session_idle_check_assignments.assert_awaited_once_with(
            case.target_statuses.session_statuses
        )
