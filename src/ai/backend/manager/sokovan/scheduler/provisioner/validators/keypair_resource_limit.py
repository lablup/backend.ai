"""Validator for keypair resource limits."""

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.types import (
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

    def name(self) -> str:
        """Return the validator name for predicates."""
        return "KeypairResourceLimitValidator"

    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "Keypair has sufficient resource quota for the requested session"

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Get the keypair's resource policy
        policy = snapshot.resource_policy.keypair_policies.get(workload.access_key)
        if not policy:
            # If no policy is defined, we can't validate - let it pass
            return

        # Get current keypair occupancy
        key_occupancy = snapshot.resource_occupancy.by_keypair.get(workload.access_key)
        if key_occupancy:
            key_occupied = key_occupancy.occupied_slots
        else:
            key_occupied = ResourceSlot()

        # Check if adding this workload would exceed the limit
        total_after = key_occupied + workload.requested_slots
        if not (total_after <= policy.total_resource_slots):
            exceeded_msg = " ".join(f"{k}={v}" for k, v in policy.total_resource_slots.items() if v)
            raise KeypairResourceQuotaExceeded(
                f"Your keypair resource quota is exceeded. ({exceeded_msg})"
            )
