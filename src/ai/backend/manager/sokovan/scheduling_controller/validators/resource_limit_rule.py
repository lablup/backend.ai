"""Per-kernel resource limit validator.

Ports the validate-side of the legacy ``ResourceCalculator``: the
resolved per-kernel ``execution_spec.resources`` list must meet the
image minimum (shmem added to ``mem``), and ``resource_opts.shmem``
must be strictly smaller than the requested memory.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any, cast, override

from ai.backend.common.types import (
    BinarySize,
    ResourceSlot,
    ResourceSlotEntry,
    SlotName,
    SlotTypes,
)
from ai.backend.manager.data.resource.types import SlotTypePolicy
from ai.backend.manager.data.session.creation import ImageInfo
from ai.backend.manager.data.session.spec import KernelSpec, SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.sokovan.scheduling_controller.resource_parse import (
    image_min_slots,
    parse_quantity,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidationContext,
    SessionSpecValidatorRule,
)


class ResourceLimitRule(SessionSpecValidatorRule):
    """Per-kernel requested slots must satisfy image min/max + shmem rules."""

    @override
    def name(self) -> str:
        return "resource_limit"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecValidationContext,
    ) -> None:
        for idx, kernel in enumerate(spec.resource_spec.kernel_specs):
            image_info = context.image_infos.get(kernel.execution_spec.resource_input.image_id)
            if image_info is None:
                continue
            self._validate_kernel(
                idx,
                kernel,
                image_info,
                context.known_slot_types,
                context.slot_type_policy,
            )

    @classmethod
    def _validate_kernel(
        cls,
        idx: int,
        kernel: KernelSpec,
        image_info: ImageInfo,
        known_slot_types: Mapping[SlotName, SlotTypes],
        policy: SlotTypePolicy,
    ) -> None:
        min_slots = image_min_slots(image_info)
        shmem = kernel.execution_spec.resource_input.resource_opts.shmem
        if shmem is not None:
            min_slots["mem"] = min_slots.get("mem", Decimal(0)) + Decimal(int(shmem))

        requested = {
            entry.resource_type: parse_quantity(entry.quantity)
            for entry in kernel.execution_spec.resource_input.resources
        }
        for slot_name, min_value in min_slots.items():
            if Decimal(min_value) <= Decimal(0):
                continue
            if SlotName(slot_name) not in policy.enabled:
                continue
            requested_value = requested.get(slot_name)
            if requested_value is None or requested_value < Decimal(min_value):
                min_repr = cls._humanize_slots(min_slots, known_slot_types)
                raise InvalidAPIParameters(
                    extra_msg=(
                        f"kernel_specs[{idx}] resource request is smaller than "
                        f"the image minimum ({min_repr})."
                    ),
                )
        if shmem is not None and "mem" in requested:
            mem_value = requested["mem"]
            if Decimal(int(shmem)) >= mem_value:
                raise InvalidAPIParameters(
                    extra_msg=(
                        f"kernel_specs[{idx}] shared-memory ({shmem!s}) must be "
                        f"smaller than requested memory ({BinarySize(mem_value)!s})."
                    ),
                )

    @staticmethod
    def _humanize_slots(
        slots: Mapping[str, Decimal],
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> str:
        if not known_slot_types:
            return " ".join(f"{k}={v}" for k, v in slots.items())
        resource_slot = ResourceSlot({k: Decimal(v) for k, v in slots.items()})
        return " ".join(
            f"{k}={v}"
            for k, v in resource_slot.to_humanized(
                cast(Mapping[str, Any], known_slot_types)
            ).items()
        )


__all__ = ["ResourceLimitRule", "ResourceSlotEntry"]
