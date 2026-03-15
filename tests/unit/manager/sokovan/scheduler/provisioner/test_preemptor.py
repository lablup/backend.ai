"""Unit tests for PreemptionCandidateSelector."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import AccessKey, PreemptionOrder, ResourceSlot, SessionId
from ai.backend.manager.sokovan.data import RunningSessionData
from ai.backend.manager.sokovan.scheduler.provisioner.preemptor import PreemptionCandidateSelector


def _make_session(
    priority: int = 5,
    is_preemptible: bool = True,
    cpu: str = "2",
    mem: str = "4096",
    created_at: datetime | None = None,
) -> RunningSessionData:
    return RunningSessionData(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("test-key"),
        priority=priority,
        is_preemptible=is_preemptible,
        occupied_slots=ResourceSlot({"cpu": Decimal(cpu), "mem": Decimal(mem)}),
        created_at=created_at or datetime.now(tzutc()),
        scaling_group_name="default",
    )


def _slots(cpu: str = "0", mem: str = "0") -> ResourceSlot:
    return ResourceSlot({"cpu": Decimal(cpu), "mem": Decimal(mem)})


class TestPreemptionCandidateSelector:
    """Tests for PreemptionCandidateSelector."""

    @pytest.fixture
    def selector(self) -> PreemptionCandidateSelector:
        return PreemptionCandidateSelector()

    def test_no_preemption_when_resources_sufficient(
        self, selector: PreemptionCandidateSelector
    ) -> None:
        """No preemption when available resources satisfy the pending session."""
        running = [_make_session(priority=3)]
        result = selector.select_candidates(
            running_sessions=running,
            pending_priority=10,
            requested_slots=_slots("2", "4096"),
            available_slots=_slots("4", "8192"),  # Enough resources
            preemptible_priority=5,
            preemption_order=PreemptionOrder.OLDEST,
        )
        assert result.candidates == []
        assert result.freed_slots == ResourceSlot()

    def test_no_preemption_when_no_preemptible_sessions(
        self, selector: PreemptionCandidateSelector
    ) -> None:
        """No preemption when no preemptible running sessions exist."""
        running = [_make_session(priority=3, is_preemptible=False)]
        result = selector.select_candidates(
            running_sessions=running,
            pending_priority=10,
            requested_slots=_slots("2", "4096"),
            available_slots=_slots("0", "0"),  # No free resources
            preemptible_priority=5,
            preemption_order=PreemptionOrder.OLDEST,
        )
        assert result.candidates == []

    def test_no_preemption_when_insufficient_candidates(
        self, selector: PreemptionCandidateSelector
    ) -> None:
        """No candidates returned when available preemptible sessions cannot cover the deficit."""
        running = [_make_session(priority=3, cpu="1", mem="1024")]
        result = selector.select_candidates(
            running_sessions=running,
            pending_priority=10,
            requested_slots=_slots("4", "8192"),  # Needs more than the candidate can provide
            available_slots=_slots("0", "0"),
            preemptible_priority=5,
            preemption_order=PreemptionOrder.OLDEST,
        )
        assert result.candidates == []

    def test_sessions_above_preemptible_priority_are_excluded(
        self, selector: PreemptionCandidateSelector
    ) -> None:
        """Sessions with priority > preemptible_priority are not preempted."""
        # Session has priority 6, preemptible_priority is 5 — should NOT be preemptible
        running = [_make_session(priority=6, is_preemptible=True, cpu="4", mem="8192")]
        result = selector.select_candidates(
            running_sessions=running,
            pending_priority=10,
            requested_slots=_slots("2", "4096"),
            available_slots=_slots("0", "0"),
            preemptible_priority=5,
            preemption_order=PreemptionOrder.OLDEST,
        )
        assert result.candidates == []

    def test_is_preemptible_false_sessions_never_preempted(
        self, selector: PreemptionCandidateSelector
    ) -> None:
        """Sessions with is_preemptible=False are never selected, regardless of priority."""
        running = [_make_session(priority=1, is_preemptible=False, cpu="4", mem="8192")]
        result = selector.select_candidates(
            running_sessions=running,
            pending_priority=10,
            requested_slots=_slots("2", "4096"),
            available_slots=_slots("0", "0"),
            preemptible_priority=5,
            preemption_order=PreemptionOrder.OLDEST,
        )
        assert result.candidates == []

    def test_lowest_priority_selected_first(self, selector: PreemptionCandidateSelector) -> None:
        """Lowest priority sessions are selected first."""
        now = datetime.now(tzutc())
        low_priority = _make_session(priority=1, cpu="2", mem="4096", created_at=now)
        high_priority = _make_session(priority=4, cpu="2", mem="4096", created_at=now)

        result = selector.select_candidates(
            running_sessions=[high_priority, low_priority],
            pending_priority=10,
            requested_slots=_slots("2", "4096"),
            available_slots=_slots("0", "0"),
            preemptible_priority=5,
            preemption_order=PreemptionOrder.OLDEST,
        )
        # Only need to preempt one session — should pick the lowest priority one
        assert len(result.candidates) == 1
        assert result.candidates[0].session_id == low_priority.session_id

    def test_preemption_order_oldest_first(self, selector: PreemptionCandidateSelector) -> None:
        """With preemption_order=oldest, oldest session (smallest created_at) is preempted first."""
        now = datetime.now(tzutc())
        older = _make_session(priority=3, cpu="2", mem="4096", created_at=now - timedelta(hours=2))
        newer = _make_session(priority=3, cpu="2", mem="4096", created_at=now - timedelta(hours=1))

        result = selector.select_candidates(
            running_sessions=[newer, older],
            pending_priority=10,
            requested_slots=_slots("2", "4096"),
            available_slots=_slots("0", "0"),
            preemptible_priority=5,
            preemption_order=PreemptionOrder.OLDEST,
        )
        assert len(result.candidates) == 1
        assert result.candidates[0].session_id == older.session_id

    def test_preemption_order_newest_first(self, selector: PreemptionCandidateSelector) -> None:
        """With preemption_order=newest, newest session (largest created_at) is preempted first."""
        now = datetime.now(tzutc())
        older = _make_session(priority=3, cpu="2", mem="4096", created_at=now - timedelta(hours=2))
        newer = _make_session(priority=3, cpu="2", mem="4096", created_at=now - timedelta(hours=1))

        result = selector.select_candidates(
            running_sessions=[older, newer],
            pending_priority=10,
            requested_slots=_slots("2", "4096"),
            available_slots=_slots("0", "0"),
            preemptible_priority=5,
            preemption_order=PreemptionOrder.NEWEST,
        )
        assert len(result.candidates) == 1
        assert result.candidates[0].session_id == newer.session_id

    def test_multiple_candidates_accumulated_until_sufficient(
        self, selector: PreemptionCandidateSelector
    ) -> None:
        """Multiple sessions are accumulated until freed resources cover the deficit."""
        now = datetime.now(tzutc())
        s1 = _make_session(priority=2, cpu="1", mem="2048", created_at=now - timedelta(hours=3))
        s2 = _make_session(priority=2, cpu="1", mem="2048", created_at=now - timedelta(hours=2))
        s3 = _make_session(priority=2, cpu="2", mem="4096", created_at=now - timedelta(hours=1))

        # Need 3 CPU and 6144 mem; each preemptible session provides 1 CPU / 2048 mem
        result = selector.select_candidates(
            running_sessions=[s1, s2, s3],
            pending_priority=10,
            requested_slots=_slots("3", "6144"),
            available_slots=_slots("0", "0"),
            preemptible_priority=5,
            preemption_order=PreemptionOrder.OLDEST,
        )
        # s1 + s2 together give 2 CPU / 4096 mem — not enough
        # s1 + s2 + s3 gives 4 CPU / 8192 mem — enough
        assert len(result.candidates) == 3

    def test_pending_priority_must_be_higher_than_preemptible(
        self, selector: PreemptionCandidateSelector
    ) -> None:
        """Pending session must have strictly higher priority than the running session."""
        running = [_make_session(priority=5, cpu="4", mem="8192")]
        # Pending session has same priority as the running session — no preemption
        result = selector.select_candidates(
            running_sessions=running,
            pending_priority=5,  # Same as running session priority
            requested_slots=_slots("2", "4096"),
            available_slots=_slots("0", "0"),
            preemptible_priority=5,
            preemption_order=PreemptionOrder.OLDEST,
        )
        assert result.candidates == []
