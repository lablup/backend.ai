"""Per-kernel validator rejecting runner-reserved environment variables."""

from __future__ import annotations

from typing import override

from ai.backend.common.docker import RUNNER_RESERVED_ENVIRON_KEYS
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class RunnerReservedEnvironRule(SessionSpecValidatorRule):
    """No kernel's environ may set a variable in ``RUNNER_RESERVED_ENVIRON_KEYS``."""

    @override
    def name(self) -> str:
        return "runner_reserved_environ"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        for kernel_idx, kernel in enumerate(spec.resource_spec.kernel_specs):
            reserved_keys = RUNNER_RESERVED_ENVIRON_KEYS & kernel.execution_spec.environ.keys()
            if reserved_keys:
                raise InvalidAPIParameters(
                    extra_msg=(
                        f"kernel_specs[{kernel_idx}].execution_spec.environ sets reserved "
                        f"variables: {', '.join(sorted(reserved_keys))}."
                    ),
                )
