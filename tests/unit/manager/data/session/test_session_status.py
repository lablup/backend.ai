from __future__ import annotations

from ai.backend.manager.data.session.types import SessionStatus


class TestPreemptedStatus:
    """Transition rules for the PREEMPTED session status (BEP-1055)."""

    def test_preempted_is_a_string_valued_status(self) -> None:
        """PREEMPTED is accepted as a session status and stored as a string."""
        assert SessionStatus("PREEMPTED") is SessionStatus.PREEMPTED
        assert SessionStatus.PREEMPTED.value == "PREEMPTED"

    def test_preempted_can_transition_to_terminating(self) -> None:
        """PREEMPTED -> TERMINATING is allowed (terminate mode)."""
        assert SessionStatus.PREEMPTED in SessionStatus.terminatable_statuses()

    def test_preempted_can_transition_to_terminated_directly(self) -> None:
        """PREEMPTED -> TERMINATED is allowed (force terminate)."""
        assert SessionStatus.PREEMPTED in SessionStatus.force_terminatable_statuses()

    def test_preempted_can_be_requeued_to_pending(self) -> None:
        """PREEMPTED -> PENDING is allowed (reschedule mode)."""
        assert SessionStatus.PREEMPTED in SessionStatus.retriable_statuses()

    def test_preempted_is_not_terminal(self) -> None:
        """PREEMPTED is a transient state, not a terminal one."""
        assert SessionStatus.PREEMPTED not in SessionStatus.terminal_statuses()
        assert not SessionStatus.PREEMPTED.is_terminal()

    def test_preempted_is_classified_transient_like_deprioritizing(self) -> None:
        """PREEMPTED mirrors DEPRIORITIZING at the transient-status enumeration point."""
        occupied = SessionStatus.resource_occupied_statuses()
        assert SessionStatus.PREEMPTED not in occupied
        assert SessionStatus.DEPRIORITIZING not in occupied

    def test_error_is_not_resource_occupying(self) -> None:
        """ERROR sessions do not count toward resource occupancy."""
        assert SessionStatus.ERROR not in SessionStatus.resource_occupied_statuses()

    def test_preemption_victim_statuses_strip_terminating(self) -> None:
        """Victim candidates occupy resources and can still be terminated;
        RESERVED is stripped — its hold belongs to another preemption plan."""
        victims = SessionStatus.preemption_victim_statuses()
        assert victims == (
            SessionStatus.resource_occupied_statuses() & SessionStatus.terminatable_statuses()
        ) - {SessionStatus.RESERVED}
        assert SessionStatus.SCHEDULED in victims
        assert SessionStatus.RUNNING in victims
        assert SessionStatus.TERMINATING not in victims
        assert SessionStatus.RESERVED not in victims
