"""Per-keypair concurrent-session limit rule.

Ports the legacy ``check_concurrency`` predicate into a pre-enqueue
validator. The scheduling controller pre-fetches
:attr:`SessionSpecValidationContext.active_session_count` via the
scheduler repository; this rule raises :class:`QuotaExceeded` when
adding one more session would push the user past the keypair policy's
``max_concurrent_sessions`` ceiling.
"""

from __future__ import annotations

from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.kernel import QuotaExceeded
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidationContext,
    SessionSpecValidatorRule,
)


class ConcurrentSessionLimitRule(SessionSpecValidatorRule):
    """Reject enqueue when the keypair is already at its concurrent-session cap."""

    def name(self) -> str:
        return "concurrent_session_limit"

    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecValidationContext,
    ) -> None:
        policy = context.keypair_resource_policy
        if policy is None:
            return
        limit = policy.max_concurrent_sessions
        if limit <= 0:
            return
        active = context.active_session_count
        if active + 1 > limit:
            raise QuotaExceeded(
                extra_msg=(
                    f"Keypair already has {active} active sessions, "
                    f"which exceeds the per-keypair concurrent-session "
                    f"limit of {limit}."
                ),
            )
