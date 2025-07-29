from ai.backend.manager.errors.scheduler import PendingSessionLimitError
from ai.backend.manager.scheduler.validators.types import ValidatorContext
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class PendingSessionCountLimitValidator(SchedulerValidator):
    """Validator to check if user has exceeded maximum pending session count."""

    @property
    def name(self) -> str:
        return "pending_session_count_limit"

    async def validate(self, context: ValidatorContext) -> None:
        """
        Check if user has exceeded the maximum pending session count.

        Raises:
            PendingSessionLimitError: If pending session count limit is exceeded
        """
        max_pending_sessions = context.keypair_resource_policy.max_pending_session_count

        if (
            max_pending_sessions is not None
            and max_pending_sessions > 0
            and len(context.pending_sessions) >= max_pending_sessions
        ):
            raise PendingSessionLimitError(
                f"You cannot create more than {max_pending_sessions} pending sessions"
            )
