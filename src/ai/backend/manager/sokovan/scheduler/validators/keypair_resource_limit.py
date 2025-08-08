"""Validator for keypair resource limits."""

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

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
        key_occupied = snapshot.resource_occupancy.by_keypair.get(
            workload.access_key, ResourceSlot()
        )

        # Check if adding this workload would exceed the limit
        total_after = key_occupied + workload.requested_slots
        if not (total_after <= policy.total_resource_slots):
            # Format the limit for human-readable output
            if policy.total_resource_slots is None:
                # None means no policy at all
                exceeded_msg = f"No resource policy found. current: {key_occupied}, requested: {workload.requested_slots}"
            elif not policy.total_resource_slots or not any(
                v for v in policy.total_resource_slots.values()
            ):
                # Empty ResourceSlot {} means unlimited - this shouldn't cause an error
                # But if we're here, it means the comparison failed for some reason
                exceeded_msg = f"Resource comparison failed (empty limit). current: {key_occupied}, requested: {workload.requested_slots}"
            else:
                limit_str = " ".join(
                    f"{k}={v}" for k, v in policy.total_resource_slots.items() if v
                )
                exceeded_msg = f"limit: {limit_str}, current: {key_occupied}, requested: {workload.requested_slots}"
            raise KeypairResourceQuotaExceeded(exceeded_msg)
