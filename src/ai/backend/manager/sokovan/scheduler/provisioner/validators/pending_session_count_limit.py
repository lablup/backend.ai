"""Validator for pending session count limits."""

from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .exceptions import PendingSessionCountLimitExceeded
from .validator import ValidatorRule


class PendingSessionCountLimitValidator(ValidatorRule):
    """
    Check if creating a new pending session would exceed the allowed count.
    This corresponds to check_pending_session_count_limit predicate.
    """

    def name(self) -> str:
        """Return the validator name for predicates."""
        return "PendingSessionCountLimitValidator"

    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "Pending session count is within the allowed limit for the access key"

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Get the keypair's resource policy
        policy = snapshot.resource_policy.keypair_policies.get(workload.access_key)
        if not policy:
            # If no policy is defined, we can't validate - let it pass
            return

        # Check if there's a pending session count limit
        pending_count_limit = policy.max_pending_session_count
        if pending_count_limit is None:
            # No limit set, allow
            return

        # Get current pending sessions for this keypair
        pending_sessions = snapshot.pending_sessions.by_keypair.get(workload.access_key, [])
        current_pending_count = len(pending_sessions)

        # Check if creating this session would exceed the limit
        if current_pending_count >= pending_count_limit:
            raise PendingSessionCountLimitExceeded(
                f"You cannot create more than {pending_count_limit} pending session(s)."
            )
