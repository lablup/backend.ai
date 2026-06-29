"""Validator for group resource limits."""

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.sokovan import SessionWorkload, SystemSnapshot

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

        # Get current group occupancy (list[SlotQuantity]) and convert to ResourceSlot
        group_occupied_quantities = snapshot.resource_occupancy.by_group.get(workload.group_id, [])
        group_occupied = ResourceSlot({
            sq.slot_name: sq.quantity for sq in group_occupied_quantities
        })

        # Check if adding this workload would exceed the limit
        total_after = group_occupied + workload.requested_slots
        if not (total_after <= group_limit):
            raise GroupResourceQuotaExceeded(quota_slots=group_limit)
