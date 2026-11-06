"""Per-slot-type session limits: exact unique amount, single node, session total.

``sealed_launch`` is not checked at enqueue.
"""

from __future__ import annotations

from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.types import ClusterMode, SlotTypes
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.kernel import QuotaExceeded
from ai.backend.manager.sokovan.scheduling_controller.resource_parse import parse_quantity
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class SlotTypeLimitRule(SessionSpecValidatorRule):
    """Requested slots must respect their slot type's session limits."""

    @override
    def name(self) -> str:
        return "slot_type_limit"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        info = context.global_info.slot_type_info
        kernel_specs = spec.resource_spec.kernel_specs
        totals: dict[ResourceSlotName, Decimal] = {}
        indices: dict[ResourceSlotName, list[int]] = {}
        unique_errors: list[str] = []
        for idx, kernel in enumerate(kernel_specs):
            for entry in kernel.execution_spec.resource_input.resources:
                slot = ResourceSlotName(entry.resource_type)
                quantity = parse_quantity(entry.quantity)
                if quantity <= Decimal(0):
                    continue
                totals[slot] = totals.get(slot, Decimal(0)) + quantity
                indices.setdefault(slot, []).append(idx)
                # Provisional: mirrors the agent's alloc_map unique check, moved to enqueue.
                if info.types.get(slot) == SlotTypes.UNIQUE and quantity != Decimal(1):
                    unique_errors.append(
                        f"kernel_specs[{idx}]: unique resource slot '{slot}' must be "
                        f"requested as exactly 1, got {entry.quantity}."
                    )
        if unique_errors:
            raise InvalidAPIParameters(extra_msg=" ".join(unique_errors))
        reasons: list[str] = []
        if len(kernel_specs) > 1:
            reasons.append(f"the session has {len(kernel_specs)} kernels")
        if spec.resource_spec.options.cluster_mode == ClusterMode.MULTI_NODE:
            reasons.append("cluster_mode is multi-node")
        node_errors = [
            f"kernel_specs{indices[slot]}: resource slot '{slot}' is limited to "
            f"single-node sessions with one kernel, but {' and '.join(reasons)}."
            for slot in totals
            if slot in info.single_node_only and reasons
        ]
        if node_errors:
            raise InvalidAPIParameters(extra_msg=" ".join(node_errors))
        for slot, total in totals.items():
            limit = info.max_per_session.get(slot)
            if limit is not None and total > limit:
                raise QuotaExceeded(
                    extra_msg=(
                        f"kernel_specs{indices[slot]}: request {total.normalize():f} of resource "
                        f"slot '{slot}', exceeding the limit of {limit.normalize():f} per session."
                    ),
                )
