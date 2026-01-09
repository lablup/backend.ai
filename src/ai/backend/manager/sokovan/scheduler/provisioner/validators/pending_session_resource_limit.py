"""Validator for pending session resource limits."""

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .exceptions import PendingSessionResourceLimitExceeded
from .validator import ValidatorRule


class PendingSessionResourceLimitValidator(ValidatorRule):
    """
    Check if creating a new pending session would exceed the allowed resource limits.
    This corresponds to check_pending_session_resource_limit predicate.
    """

    def name(self) -> str:
        """Return the validator name for predicates."""
        return "PendingSessionResourceLimitValidator"

    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "Pending session resource usage is within the allowed limit for the access key"

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Get the keypair's resource policy
        policy = snapshot.resource_policy.keypair_policies.get(workload.access_key)
        if not policy:
            # If no policy is defined, we can't validate - let it pass
            return

        # Check if there's a pending session resource limit
        pending_resource_limit = policy.max_pending_session_resource_slots
        if not pending_resource_limit:
            # No limit set, allow
            return

        # Calculate current pending session resource usage
        pending_sessions = snapshot.pending_sessions.by_keypair.get(workload.access_key, [])
        current_pending_slots = ResourceSlot()
        for session in pending_sessions:
            current_pending_slots += session.requested_slots

        # Check if adding this workload would exceed the limit
        total_after = current_pending_slots
        if total_after > pending_resource_limit:
            # Format the current usage for human-readable output
            usage_str = " ".join(f"{k}={v}" for k, v in current_pending_slots.items() if v)
            raise PendingSessionResourceLimitExceeded(
                f"Your pending session quota is exceeded. ({usage_str})"
            )
