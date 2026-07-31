"""Per-user scheduling-priority cap rule.

Bounds the *global* scheduler ``priority`` a user may declare at enqueue
time via the ``max_priority`` ceiling of the user's main keypair policy.
The scope-local ``job_priority`` only ranks the owner's own sessions and
is therefore deliberately left uncapped.
"""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.kernel import QuotaExceeded
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class PriorityLimitRule(SessionSpecValidatorRule):
    """Reject enqueue when the requested priority exceeds the user's cap."""

    @override
    def name(self) -> str:
        return "priority_limit"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        policy = context.user.policy
        if policy is None:
            return
        limit = policy.max_priority
        if limit is None:
            return
        requested = spec.resource_spec.options.priority
        if requested > limit:
            raise QuotaExceeded(
                extra_msg=(
                    f"The requested session priority {requested} "
                    f"exceeds the allowed maximum priority of {limit}."
                ),
            )
