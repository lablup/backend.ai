from ai.backend.common.types import ResourceSlot
from ai.backend.manager.errors.scheduler import ResourceQuotaExceededError
from ai.backend.manager.scheduler.validators.types import ValidatorContext
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class PendingSessionResourceLimitValidator(SchedulerValidator):
    """Validator to check if user has exceeded pending session resource limit."""

    @property
    def name(self) -> str:
        return "pending_session_resource_limit"

    async def validate(self, context: ValidatorContext) -> None:
        """
        Check if user's pending sessions exceed the resource limit.

        Raises:
            ResourceQuotaExceededError: If pending session resource limit is exceeded
        """
        max_pending_resource_slots = ResourceSlot.from_policy(
            {
                "max_pending_session_resource_slots": context.keypair_resource_policy.max_pending_session_resource_slots,
            },
            context.known_slot_types,
        )

        # Calculate total resources of pending sessions
        total_pending_resources = ResourceSlot()
        for session in context.pending_sessions:
            total_pending_resources += session.requested_slots

        # Add the current session's requested resources
        total_pending_with_current = total_pending_resources + context.session_data.requested_slots

        if not (total_pending_with_current <= max_pending_resource_slots):
            quota_details = " ".join(
                f"{k}={v}"
                for k, v in max_pending_resource_slots.to_humanized(
                    context.known_slot_types
                ).items()
            )
            raise ResourceQuotaExceededError(
                f"Your pending session resources are exceeded. ({quota_details})"
            )
