"""Validator for user resource limits."""

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .exceptions import UserResourcePolicyNotFound, UserResourceQuotaExceeded
from .validator import ValidatorRule


class UserResourceLimitValidator(ValidatorRule):
    """
    Check if a session would exceed the user's resource quota.
    This corresponds to check_user_resource_limit predicate.
    """

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Get the user's resource policy
        policy = snapshot.resource_policy.user_policies.get(workload.user_uuid)
        if not policy:
            raise UserResourcePolicyNotFound(
                f"User has no resource policy (uid: {workload.user_uuid})"
            )

        # Get current user occupancy
        user_occupied = snapshot.resource_occupancy.by_user.get(workload.user_uuid, ResourceSlot())

        # Check if adding this workload would exceed the limit
        total_after = user_occupied + workload.requested_slots
        if not (total_after <= policy.total_resource_slots):
            # Format the limit for human-readable output
            limit_str = " ".join(f"{k}={v}" for k, v in policy.total_resource_slots.items() if v)
            raise UserResourceQuotaExceeded(
                f"Your main-keypair resource quota is exceeded. ({limit_str})"
            )
