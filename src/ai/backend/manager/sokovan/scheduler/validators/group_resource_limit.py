"""Validator for group resource limits."""

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .exceptions import GroupResourceQuotaExceeded
from .validator import ValidatorRule


class GroupResourceLimitValidator(ValidatorRule):
    """
    Check if a session would exceed the group's resource quota.
    This corresponds to check_group_resource_limit predicate.
    """

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Get the group's resource limit
        group_limit = snapshot.resource_policy.group_limits.get(workload.group_id)
        if not group_limit:
            # If no limit is defined, we can't validate - let it pass
            return

        # Get current group occupancy
        group_occupied = snapshot.resource_occupancy.by_group.get(workload.group_id, ResourceSlot())

        # Check if adding this workload would exceed the limit
        total_after = group_occupied + workload.requested_slots
        if not (total_after <= group_limit):
            # Format the limit for human-readable output
            limit_str = " ".join(f"{k}={v}" for k, v in group_limit.items() if v)
            raise GroupResourceQuotaExceeded(
                f"Your group resource quota is exceeded. ({limit_str})"
            )
