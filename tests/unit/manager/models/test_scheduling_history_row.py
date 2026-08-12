"""Tests for the scheduling-history merge rule."""

from __future__ import annotations

import uuid

import pytest

from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow

SESSION_ID = SessionId(uuid.uuid4())


def _make_history(
    *,
    result: SchedulingResult,
    phase: str = "schedule-sessions",
    to_status: SessionStatus = SessionStatus.PENDING,
    error_code: str | None = None,
) -> SessionSchedulingHistoryRow:
    return SessionSchedulingHistoryRow(
        session_id=SESSION_ID,
        phase=phase,
        from_status=str(SessionStatus.PENDING),
        to_status=str(to_status),
        result=str(result),
        error_code=error_code,
        message="",
        sub_steps=[],
        attempts=1,
    )


class TestSessionSchedulingHistoryMerge:
    """``attempts`` drives the give-up (deprioritization) classification, so
    what merges into one record decides what counts as a retry."""

    @pytest.fixture
    def failure(self) -> SessionSchedulingHistoryRow:
        return _make_history(result=SchedulingResult.NEED_RETRY)

    def test_same_result_merges(self, failure: SessionSchedulingHistoryRow) -> None:
        assert failure.should_merge_with(_make_history(result=SchedulingResult.NEED_RETRY))

    @pytest.mark.parametrize(
        "later_result",
        [SchedulingResult.GIVE_UP, SchedulingResult.EXPIRED, SchedulingResult.SUCCESS],
    )
    def test_another_attempt_result_still_merges(
        self,
        failure: SessionSchedulingHistoryRow,
        later_result: SchedulingResult,
    ) -> None:
        """Which attempt result was recorded is not part of the merge key.

        Handlers that declare no transition for give_up/expired record them
        with an unchanged ``to_status``; splitting those off would reset the
        retry budget every time give_up fires, so it could never stick.
        """
        assert failure.should_merge_with(_make_history(result=later_result))

    def test_skip_does_not_merge_into_an_attempt(
        self, failure: SessionSchedulingHistoryRow
    ) -> None:
        """A session that was never tried may not inflate the retry counter."""
        assert not failure.should_merge_with(_make_history(result=SchedulingResult.SKIPPED))

    def test_attempt_does_not_merge_into_a_skip(self) -> None:
        skipped = _make_history(result=SchedulingResult.SKIPPED)

        assert not skipped.should_merge_with(_make_history(result=SchedulingResult.NEED_RETRY))

    def test_different_phase_does_not_merge(self, failure: SessionSchedulingHistoryRow) -> None:
        assert not failure.should_merge_with(
            _make_history(result=SchedulingResult.NEED_RETRY, phase="start-sessions")
        )

    def test_different_error_code_does_not_merge(
        self, failure: SessionSchedulingHistoryRow
    ) -> None:
        assert not failure.should_merge_with(
            _make_history(result=SchedulingResult.NEED_RETRY, error_code="E-1")
        )
