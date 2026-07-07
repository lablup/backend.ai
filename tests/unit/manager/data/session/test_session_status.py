from __future__ import annotations

from ai.backend.manager.data.session.types import SessionStatus


class TestPreemptedStatus:
    """Transition rules for the PREEMPTED session status (BEP-1055)."""

    def test_preempted_is_a_string_valued_status(self) -> None:
        """PREEMPTED is accepted as a session status and stored as a string."""
        assert SessionStatus("PREEMPTED") is SessionStatus.PREEMPTED
        assert SessionStatus.PREEMPTED.value == "PREEMPTED"

    def test_only_running_can_transition_to_preempted(self) -> None:
        """RUNNING -> PREEMPTED is allowed; every other source is rejected."""
        assert SessionStatus.preemptable_statuses() == frozenset((SessionStatus.RUNNING,))
        # Illegal sources are not eligible to be marked PREEMPTED.
        for illegal_source in (
            SessionStatus.PENDING,
            SessionStatus.SCHEDULED,
            SessionStatus.PREPARING,
            SessionStatus.CREATING,
            SessionStatus.TERMINATING,
            SessionStatus.TERMINATED,
            SessionStatus.PREEMPTED,
        ):
            assert illegal_source not in SessionStatus.preemptable_statuses()

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
