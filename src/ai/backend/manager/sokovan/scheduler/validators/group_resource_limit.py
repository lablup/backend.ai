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

    def name(self) -> str:
        """Return the validator name for predicates."""
        return "GroupResourceLimitValidator"

    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "Group has sufficient resource quota for the requested session"

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
            if group_limit and any(v for v in group_limit.values()):
                limit_str = " ".join(f"{k}={v}" for k, v in group_limit.items() if v)
                exceeded_msg = f"limit: {limit_str}, current: {group_occupied}, requested: {workload.requested_slots}"
            else:
                exceeded_msg = f"No resource limits defined. current: {group_occupied}, requested: {workload.requested_slots}"
            raise GroupResourceQuotaExceeded(
                f"Your group resource quota is exceeded. ({exceeded_msg})"
            )
