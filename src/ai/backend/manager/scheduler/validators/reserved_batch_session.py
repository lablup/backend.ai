from datetime import datetime

from dateutil.tz import tzutc

from ai.backend.common.types import SessionTypes
from ai.backend.manager.errors.scheduler import ReservedBatchSessionError
from ai.backend.manager.scheduler.validators.types import ValidatorContext
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class ReservedBatchSessionValidator(SchedulerValidator):
    """Validator to check if a batch-type session should not be started before its scheduled time."""

    @property
    def name(self) -> str:
        return "reserved_batch_session"

    async def validate(self, context: ValidatorContext) -> None:
        """
        Check if a batch-type session should not be started for a certain amount of time.

        Raises:
            ReservedBatchSessionError: If batch session is before its scheduled start time
        """
        if SessionTypes(context.session_data.session_type) == SessionTypes.BATCH:
            if (
                context.session_starts_at is not None
                and datetime.now(tzutc()) < context.session_starts_at
            ):
                raise ReservedBatchSessionError("Before start time")
