from ai.backend.manager.errors.scheduler import ConcurrencyLimitError
from ai.backend.manager.scheduler.validators.types import ValidatorContext
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class ConcurrencyValidator(SchedulerValidator):
    """Validator to check if user has reached maximum concurrent session limit."""

    @property
    def name(self) -> str:
        return "concurrency"

    async def validate(self, context: ValidatorContext) -> None:
        """
        Check if user has reached the maximum concurrent session limit.

        Raises:
            ConcurrencyLimitError: If concurrent session limit is exceeded
        """
        if context.session_data.session_type.is_private():
            max_concurrent_sessions = context.keypair_resource_policy.max_concurrent_sftp_sessions
        else:
            max_concurrent_sessions = context.keypair_resource_policy.max_concurrent_sessions

        if context.keypair_concurrency_used >= max_concurrent_sessions:
            raise ConcurrencyLimitError(
                f"You cannot run more than {max_concurrent_sessions} concurrent sessions"
            )
