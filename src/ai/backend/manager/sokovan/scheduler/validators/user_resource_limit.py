"""Validator for user resource limits."""

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .exceptions import UserResourceQuotaExceeded
from .validator import ValidatorRule


class UserResourceLimitValidator(ValidatorRule):
    """
    Check if a session would exceed the user's resource quota.
    This corresponds to check_user_resource_limit predicate.
    """

    def name(self) -> str:
        """Return the validator name for predicates."""
        return "UserResourceLimitValidator"

    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "User has sufficient resource quota for the requested session"

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Get the user's resource policy
        policy = snapshot.resource_policy.user_policies.get(workload.user_uuid)
        if not policy:
            # If no user-specific policy, skip validation (no limits apply)
            return

        # Get current user occupancy
        user_occupied = snapshot.resource_occupancy.by_user.get(workload.user_uuid, ResourceSlot())

        # Check if adding this workload would exceed the limit
        total_after = user_occupied + workload.requested_slots
        if not (total_after <= policy.total_resource_slots):
            exceeded_msg = " ".join(f"{k}={v}" for k, v in policy.total_resource_slots.items() if v)
            raise UserResourceQuotaExceeded(
                f"Your main-keypair resource quota is exceeded. ({exceeded_msg})"
            )
