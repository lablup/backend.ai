"""Validator for reserved batch sessions."""

from typing import override

from ai.backend.common.types import SessionTypes
from ai.backend.manager.views.sokovan.snapshot import SystemSnapshot
from ai.backend.manager.views.sokovan.workload import SessionWorkload

from .exceptions import ReservedBatchSessionNotReady
from .validator import ValidatorRule


class ReservedBatchSessionValidator(ValidatorRule):
    """
    Check if a batch-type session should not be started for a certain amount of time.
    This corresponds to check_reserved_batch_session predicate.
    """

    @override
    def name(self) -> str:
        """Return the validator name for predicates."""
        return "ReservedBatchSessionValidator"

    @override
    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "Batch session has reached its scheduled start time"

    @override
    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Check if this is a batch session with a scheduled start time
        if workload.session_type == SessionTypes.BATCH and workload.requested_starts_at is not None:
            # Compare against the DB-sourced snapshot time, not a per-server clock
            if snapshot.observed_at < workload.requested_starts_at:
                raise ReservedBatchSessionNotReady(scheduled_start=workload.requested_starts_at)
