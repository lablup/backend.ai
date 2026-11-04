"""Per-kernel validator rejecting runner-reserved environment variables."""

from __future__ import annotations

from ai.backend.common.docker import RUNNER_RESERVED_ENVIRON_KEYS
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidationContext,
    SessionSpecValidatorRule,
)


class RunnerReservedEnvironRule(SessionSpecValidatorRule):
    """No kernel's environ may set a variable in ``RUNNER_RESERVED_ENVIRON_KEYS``."""

    def name(self) -> str:
        return "runner_reserved_environ"

    def validate(
        self,
        spec: SessionSpec,
        _context: SessionSpecValidationContext,
    ) -> None:
        for kernel_idx, kernel in enumerate(spec.kernel_specs):
            reserved_keys = RUNNER_RESERVED_ENVIRON_KEYS & kernel.execution_spec.environ.keys()
            if reserved_keys:
                raise InvalidAPIParameters(
                    extra_msg=(
                        f"kernel_specs[{kernel_idx}].execution_spec.environ sets reserved "
                        f"variables: {', '.join(sorted(reserved_keys))}."
                    ),
                )
