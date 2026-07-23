"""Required resource-slot validator.

Required slot names come from ``resource_slot_types.required``. The
preparer chain runs first, so image-minimum fallback for intrinsic slots
has already had a chance to fill ``cpu`` / ``mem`` before this rule checks
the finalized ``SessionSpec``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import override

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.sokovan.scheduling_controller.resource_parse import parse_quantity
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class RequiredResourceSlotRule(SessionSpecValidatorRule):
    """Every kernel request must include all globally required slots."""

    @override
    def name(self) -> str:
        return "required_resource_slot"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        required = context.global_info.slot_type_info.required
        if not required:
            return

        for idx, kernel in enumerate(spec.resource_spec.kernel_specs):
            requested = {
                entry.resource_type: parse_quantity(entry.quantity)
                for entry in kernel.execution_spec.resource_input.resources
            }
            missing = sorted(
                str(slot_name)
                for slot_name in required
                if requested.get(ResourceSlotName(str(slot_name)), Decimal(0)) <= Decimal(0)
            )
            if missing:
                raise InvalidAPIParameters(
                    extra_msg=(
                        f"kernel_specs[{idx}].execution_spec.resources is missing "
                        f"required resource slot(s): {missing}."
                    )
                )
