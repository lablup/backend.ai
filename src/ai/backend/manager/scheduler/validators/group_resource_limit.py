from ai.backend.common.types import ResourceSlot
from ai.backend.manager.errors.scheduler import ResourceQuotaExceededError
from ai.backend.manager.scheduler.validators.types import ValidatorContext
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class GroupResourceLimitValidator(SchedulerValidator):
    """Validator to check if group has sufficient resource quota."""

    @property
    def name(self) -> str:
        return "group_resource_limit"

    async def validate(self, context: ValidatorContext) -> None:
        """
        Check if group has sufficient resource quota.

        Raises:
            ResourceQuotaExceededError: If group resource quota is exceeded
        """
        resource_policy_map = {
            "total_resource_slots": context.group_resource_policy.total_resource_slots,
            "default_for_unspecified": context.group_resource_policy.default_for_unspecified,
        }
        total_group_allowed = ResourceSlot.from_policy(
            resource_policy_map, context.known_slot_types
        )

        if not (
            context.group_occupancy + context.session_data.requested_slots <= total_group_allowed
        ):
            group_name = context.group_name
            quota_details = " ".join(
                f"{k}={v}"
                for k, v in total_group_allowed.to_humanized(context.known_slot_types).items()
            )
            raise ResourceQuotaExceededError(
                f'Project "{group_name}" resource quota is exceeded. ({quota_details})'
            )
