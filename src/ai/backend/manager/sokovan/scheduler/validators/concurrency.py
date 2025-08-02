"""Validator for concurrent session limits."""

from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .exceptions import ConcurrencyLimitExceeded
from .validator import ValidatorRule


class ConcurrencyValidator(ValidatorRule):
    """
    Check if a session would exceed the maximum concurrent sessions allowed for a keypair.
    This corresponds to check_concurrency predicate.
    """

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Get the keypair's resource policy
        policy = snapshot.resource_policy.keypair_policies.get(workload.access_key)
        if not policy:
            # If no policy is defined, we can't validate - let it pass
            return

        # Get current session count
        current_sessions = snapshot.concurrency.sessions_by_keypair.get(workload.access_key, 0)
        current_sftp_sessions = snapshot.concurrency.sftp_sessions_by_keypair.get(
            workload.access_key, 0
        )

        # Check the appropriate limit based on session type
        if workload.is_private:
            max_sessions = policy.max_concurrent_sftp_sessions
            current_count = current_sftp_sessions
            session_type = "SFTP"
        else:
            max_sessions = policy.max_concurrent_sessions
            current_count = current_sessions
            session_type = "concurrent"

        if current_count >= max_sessions:
            raise ConcurrencyLimitExceeded(
                f"You cannot run more than {max_sessions} {session_type} sessions"
            )
