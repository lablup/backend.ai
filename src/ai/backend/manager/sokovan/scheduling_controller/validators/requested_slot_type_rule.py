"""User-requested slot-type compatibility validator.

Every ``resource_type`` in a kernel's requested resource list must be
served by some non-terminated agent in the requested resource group.
The context's ``known_slot_types`` is sourced from ``agent_resources``
joined with ``agents`` (status != TERMINATED) and
``resource_slot_types``, so it reflects the RG's hardware inventory and
the registered unit metadata in one mapping.

When the RG has no non-terminated agents the request is rejected
outright — an empty inventory cannot satisfy any caller-supplied
request and would otherwise let the session reach the scheduler only
to fail there.
"""

from __future__ import annotations

from decimal import Decimal
from typing import override

from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionSpecContext,
)
from ai.backend.manager.sokovan.scheduling_controller.resource_parse import parse_quantity
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)


class RequestedSlotTypeRule(SessionSpecValidatorRule):
    """Requested slot keys must be served by an agent in the target RG."""

    @override
    def name(self) -> str:
        return "requested_slot_type"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        rg_slot_types = context.known_slot_types
        if not rg_slot_types:
            raise InvalidAPIParameters(
                extra_msg=(
                    f"resource group '{spec.scope.resource_group_name}' has no "
                    f"agents serving any resource slot."
                ),
            )
        errors: list[str] = []
        for idx, kernel in enumerate(spec.resource_spec.kernel_specs):
            unknown = sorted({
                entry.resource_type
                for entry in kernel.execution_spec.resource_input.resources
                if entry.resource_type not in rg_slot_types
                and parse_quantity(entry.quantity) > Decimal(0)
            })
            if unknown:
                errors.append(
                    f"kernel_specs[{idx}]: the request asks for resource "
                    f"slot(s) {unknown} that resource group "
                    f"'{spec.scope.resource_group_name}' does not serve. "
                    f"Drop these slots from the request or switch to a "
                    f"resource group that supports them."
                )
        if errors:
            raise InvalidAPIParameters(extra_msg=" ".join(errors))
