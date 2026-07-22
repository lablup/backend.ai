"""Per-keypair container limit rule."""

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


class ContainerLimitRule(SessionSpecValidatorRule):
    """Session's total kernel count must not exceed the keypair limit."""

    @override
    def name(self) -> str:
        return "container_limit"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        policy = context.user.policy
        if policy is None:
            return
        limit = policy.max_containers_per_session
        if limit <= 0:
            return
        count = len(spec.resource_spec.kernel_specs)
        if count > limit:
            raise QuotaExceeded(
                extra_msg=(
                    f"Session requests {count} kernels, exceeding the "
                    f"keypair limit of {limit} containers per session."
                ),
            )
