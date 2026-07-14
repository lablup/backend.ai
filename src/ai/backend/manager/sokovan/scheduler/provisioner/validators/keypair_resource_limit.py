"""Validator for keypair resource limits."""

from typing import override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.sokovan import (
    SessionWorkload,
    SystemSnapshot,
)

from .exceptions import KeypairResourceQuotaExceeded
from .validator import ValidatorRule


class KeypairResourceLimitValidator(ValidatorRule):
    """
    Check if a session would exceed the keypair's resource quota.
    This corresponds to check_keypair_resource_limit predicate.
    """

    @override
    def name(self) -> str:
        """Return the validator name for predicates."""
        return "KeypairResourceLimitValidator"

    @override
    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "Keypair has sufficient resource quota for the requested session"

    @override
    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Get the keypair's resource policy
        policy = snapshot.resource_policy.keypair_policies.get(workload.access_key)
        if not policy:
            # If no policy is defined, we can't validate - let it pass
            return

        # Get current keypair occupancy (occupied_slots is list[SlotQuantity])
        key_occupancy = snapshot.resource_occupancy.by_keypair.get(workload.access_key)
        if key_occupancy:
            key_occupied = ResourceSlot({
                sq.slot_name: sq.quantity for sq in key_occupancy.occupied_slots
            })
        else:
            key_occupied = ResourceSlot()

        # Check if adding this workload would exceed the limit
        total_after = key_occupied + workload.requested_slots
        if not (total_after <= policy.total_resource_slots):
            raise KeypairResourceQuotaExceeded(quota_slots=policy.total_resource_slots)
