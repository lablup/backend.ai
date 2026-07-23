"""Per-user pending-session resource-slot limit rule.

The resource-side counterpart of ``PendingSessionCountLimitRule``: the
total resource slots parked in a user's pending queue are bounded at
enqueue time by the ``max_pending_session_resource_slots`` ceiling of
the user's main keypair policy. Only the slot names the policy lists
are capped; slots absent from the policy stay unbounded.
"""

from __future__ import annotations

from decimal import Decimal
from typing import override

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.kernel import QuotaExceeded
from ai.backend.manager.sokovan.scheduling_controller.resource_parse import (
    parse_quantity,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class PendingSessionResourceLimitRule(SessionSpecValidatorRule):
    """Reject enqueue when the pending queue's slot total would exceed its cap."""

    @override
    def name(self) -> str:
        return "pending_session_resource_limit"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        policy = context.user.policy
        if policy is None:
            return
        limit = policy.max_pending_session_resource_slots
        if limit is None:
            return
        requested: dict[ResourceSlotName, Decimal] = {}
        for kernel in spec.resource_spec.kernel_specs:
            for entry in kernel.execution_spec.resource_input.resources:
                slot_name = entry.resource_type
                requested[slot_name] = requested.get(slot_name, Decimal(0)) + parse_quantity(
                    entry.quantity
                )
        pending = context.user.pending_session_resource_slots
        totals = {
            slot_name: pending.get(slot_name, Decimal(0)) + requested.get(slot_name, Decimal(0))
            for slot_name in limit
        }
        exceeded = [slot_name for slot_name, total in totals.items() if total > limit[slot_name]]
        if exceeded:
            total_repr = ", ".join(f"{name}={totals[name]}" for name in exceeded)
            limit_repr = ", ".join(f"{name}={limit[name]}" for name in exceeded)
            raise QuotaExceeded(
                extra_msg=(
                    f"Your pending sessions would occupy {total_repr}, "
                    f"which exceeds the pending-session resource limit of {limit_repr}."
                ),
            )
