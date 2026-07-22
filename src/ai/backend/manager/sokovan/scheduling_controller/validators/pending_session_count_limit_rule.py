"""Per-user pending-session count limit rule.

Bounds the depth of a user's pending queue at enqueue time. Concurrent
session limits are deliberately NOT enforced here: an over-limit session
simply waits in the queue and is admitted by the scheduler-side
``ResourcePolicyValidator`` once an existing session finishes. What must
be bounded at enqueue is the queue itself, via the
``max_pending_session_count`` ceiling of the user's main keypair policy.
"""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.kernel import QuotaExceeded
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionSpecContext,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)


class PendingSessionCountLimitRule(SessionSpecValidatorRule):
    """Reject enqueue when the user's pending queue is already at its cap."""

    @override
    def name(self) -> str:
        return "pending_session_count_limit"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        policy = context.user.policy
        if policy is None:
            return
        limit = policy.max_pending_session_count
        if limit is None or limit <= 0:
            return
        pending = context.user.pending_session_count
        if pending + 1 > limit:
            raise QuotaExceeded(
                extra_msg=(
                    f"You already have {pending} pending sessions, "
                    f"which exceeds the pending-session limit of {limit}."
                ),
            )
