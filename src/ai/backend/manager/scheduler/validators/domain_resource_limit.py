from ai.backend.common.types import ResourceSlot
from ai.backend.manager.errors.scheduler import ResourceQuotaExceededError
from ai.backend.manager.scheduler.validators.types import ValidatorContext
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class DomainResourceLimitValidator(SchedulerValidator):
    """Validator to check if domain has sufficient resource quota."""

    @property
    def name(self) -> str:
        return "domain_resource_limit"

    async def validate(self, context: ValidatorContext) -> None:
        """
        Check if domain has sufficient resource quota.

        Raises:
            ResourceQuotaExceededError: If domain resource quota is exceeded
        """
        resource_policy_map = {
            "total_resource_slots": context.domain_resource_policy.total_resource_slots,
            "default_for_unspecified": context.domain_resource_policy.default_for_unspecified,
        }
        total_domain_allowed = ResourceSlot.from_policy(
            resource_policy_map, context.known_slot_types
        )

        if not (
            context.domain_occupancy + context.session_data.requested_slots <= total_domain_allowed
        ):
            domain_name = context.user_data.domain_name
            quota_details = " ".join(
                f"{k}={v}"
                for k, v in total_domain_allowed.to_humanized(context.known_slot_types).items()
            )
            raise ResourceQuotaExceededError(
                f'Domain "{domain_name}" resource quota is exceeded. ({quota_details})'
            )
