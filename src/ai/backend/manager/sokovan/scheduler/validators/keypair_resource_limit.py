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
            limit_str = " ".join(f"{k}={v}" for k, v in policy.total_resource_slots.items() if v)
            raise KeypairResourceQuotaExceeded(
                f"Your keypair resource quota is exceeded. ({limit_str})"
            )
