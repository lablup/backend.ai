"""Image-declared slot-type compatibility validator.

Every slot key declared in an image's ``resource_spec`` must be served
by some non-terminated agent in the requested resource group. The
context's ``known_slot_types`` is sourced from
``agent_resources`` joined with ``agents`` (status != TERMINATED) and
``resource_slot_types``, so it reflects the RG's hardware inventory and
the registered unit metadata in one mapping.

When the RG has no non-terminated agents the request is rejected
outright — an empty inventory cannot satisfy any image declaration and
would otherwise let the session reach the scheduler only to fail there.
"""

from __future__ import annotations

from decimal import Decimal
from typing import override

from ai.backend.common.types import SlotName
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.sokovan.scheduling_controller.resource_parse import image_min_slots
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidationContext,
    SessionSpecValidatorRule,
)


class ImageSlotTypeRule(SessionSpecValidatorRule):
    """Image-declared slot keys must be served by an agent in the target RG."""

    @override
    def name(self) -> str:
        return "image_slot_type"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecValidationContext,
    ) -> None:
        known_slot_types = context.known_slot_types
        enabled = context.slot_type_policy.enabled
        if not known_slot_types:
            raise InvalidAPIParameters(
                extra_msg=(
                    f"resource group '{spec.scope.resource_group_name}' has no "
                    f"agents serving any resource slot."
                ),
            )
        errors: list[str] = []
        for idx, kernel in enumerate(spec.kernel_specs):
            image_info = context.image_infos.get(kernel.execution_spec.image_id)
            if image_info is None:
                continue
            min_slots = image_min_slots(image_info)
            unknown = sorted(
                slot_name
                for slot_name in image_info.resource_spec
                if SlotName(slot_name) in enabled
                and SlotName(slot_name) not in known_slot_types
                and min_slots.get(slot_name, Decimal(0)) > Decimal(0)
            )
            if unknown:
                errors.append(
                    f"kernel_specs[{idx}]: image '{image_info.canonical}' "
                    f"requires resource slot(s) {unknown} that resource "
                    f"group '{spec.scope.resource_group_name}' does not "
                    f"serve. Pick an image whose required slots are "
                    f"available here, or switch to a resource group that "
                    f"supports these slots."
                )
        if errors:
            raise InvalidAPIParameters(extra_msg=" ".join(errors))
