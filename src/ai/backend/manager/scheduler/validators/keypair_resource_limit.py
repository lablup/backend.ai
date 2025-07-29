from ai.backend.common.types import ResourceSlot
from ai.backend.manager.errors.scheduler import ResourceQuotaExceededError
from ai.backend.manager.scheduler.validators.types import ValidatorContext
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class KeypairResourceLimitValidator(SchedulerValidator):
    """Validator to check if keypair has sufficient resource quota."""

    @property
    def name(self) -> str:
        return "keypair_resource_limit"

    async def validate(self, context: ValidatorContext) -> None:
        """
        Check if keypair has sufficient resource quota.

        Raises:
            ResourceQuotaExceededError: If keypair resource quota is exceeded
        """
        resource_policy_map = {
            "total_resource_slots": context.keypair_resource_policy.total_resource_slots,
            "default_for_unspecified": context.keypair_resource_policy.default_for_unspecified,
        }
        total_keypair_allowed = ResourceSlot.from_policy(
            resource_policy_map, context.known_slot_types
        )

        if not (
            context.keypair_occupancy + context.session_data.requested_slots
            <= total_keypair_allowed
        ):
            quota_details = " ".join(
                f"{k}={v}"
                for k, v in total_keypair_allowed.to_humanized(context.known_slot_types).items()
            )
            raise ResourceQuotaExceededError(
                f"Your keypair resource quota is exceeded. ({quota_details})"
            )
