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
            # Format the limit for human-readable output
            if policy.total_resource_slots is None:
                # None means no policy at all
                exceeded_msg = f"No resource policy found. current: {user_occupied}, requested: {workload.requested_slots}"
            elif not policy.total_resource_slots or not any(
                v for v in policy.total_resource_slots.values()
            ):
                # Empty ResourceSlot {} means unlimited - this shouldn't cause an error
                # But if we're here, it means the comparison failed for some reason
                exceeded_msg = f"Resource comparison failed (empty limit). current: {user_occupied}, requested: {workload.requested_slots}"
            else:
                limit_str = " ".join(
                    f"{k}={v}" for k, v in policy.total_resource_slots.items() if v
                )
                exceeded_msg = f"limit: {limit_str}, current: {user_occupied}, requested: {workload.requested_slots}"
            raise UserResourceQuotaExceeded(exceeded_msg)
