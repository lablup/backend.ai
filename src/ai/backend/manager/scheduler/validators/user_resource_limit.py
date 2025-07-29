from ai.backend.common.types import ResourceSlot
from ai.backend.manager.errors.scheduler import ResourceQuotaExceededError
from ai.backend.manager.scheduler.validators.types import ValidatorContext
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class UserResourceLimitValidator(SchedulerValidator):
    """Validator to check if user's main keypair has sufficient resource quota."""

    @property
    def name(self) -> str:
        return "user_resource_limit"

    async def validate(self, context: ValidatorContext) -> None:
        """
        Check if user's main keypair has sufficient resource quota.

        Raises:
            ResourceQuotaExceededError: If user's main keypair resource quota is exceeded
        """
        if context.user_main_keypair_resource_policy is None:
            raise ResourceQuotaExceededError(
                f"User has no main-keypair or the main-keypair has no keypair resource policy (uid: {context.session_data.user_uuid})"
            )

        resource_policy_map = {
            "total_resource_slots": context.user_main_keypair_resource_policy.total_resource_slots,
            "default_for_unspecified": context.user_main_keypair_resource_policy.default_for_unspecified,
        }
        total_main_keypair_allowed = ResourceSlot.from_policy(
            resource_policy_map, context.known_slot_types
        )

        if not (
            context.user_occupancy + context.session_data.requested_slots
            <= total_main_keypair_allowed
        ):
            quota_details = " ".join(
                f"{k}={v}"
                for k, v in total_main_keypair_allowed.to_humanized(
                    context.known_slot_types
                ).items()
            )
            raise ResourceQuotaExceededError(
                f"Your main-keypair resource quota is exceeded. ({quota_details})"
            )
