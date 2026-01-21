"""Validator for reserved batch sessions."""

from datetime import datetime

from dateutil.tz import tzutc

from ai.backend.common.types import SessionTypes
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .exceptions import SchedulingValidationError
from .validator import ValidatorRule


class ReservedBatchSessionValidator(ValidatorRule):
    """
    Check if a batch-type session should not be started for a certain amount of time.
    This corresponds to check_reserved_batch_session predicate.
    """

    def name(self) -> str:
        """Return the validator name for predicates."""
        return "ReservedBatchSessionValidator"

    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "Batch session has reached its scheduled start time"

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Check if this is a batch session with a scheduled start time
        if workload.session_type == SessionTypes.BATCH and workload.starts_at is not None:
            # Check if the current time is before the scheduled start time
            if datetime.now(tzutc()) < workload.starts_at:
                raise SchedulingValidationError("Before start time")
