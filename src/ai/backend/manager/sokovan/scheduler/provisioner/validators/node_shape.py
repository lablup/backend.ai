"""Validator that keeps a session no node of its compute cluster can hold in the queue."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.manager.sokovan.scheduler.provisioner.validators.exceptions import (
    NoNodeShapeFits,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.validator import (
    ValidatorRule,
)
from ai.backend.manager.views.sokovan.snapshot import SystemSnapshot
from ai.backend.manager.views.sokovan.workload import SessionWorkload


def _fits(
    request: Mapping[ResourceSlotName, Decimal], shape: Mapping[ResourceSlotName, Decimal]
) -> bool:
    return all(
        amount <= shape.get(slot_name, Decimal(0))
        for slot_name, amount in request.items()
        if amount > 0
    )


class NodeShapeValidator(ValidatorRule):
    """Every kernel must fit on at least one node shape of the group's compute cluster.

    The compute cluster registers as one agent, so the agent's aggregate capacity can hold a
    kernel no single node holds. Applies only when the snapshot carries node shapes, which
    only a `kubernetes` resource group with reported shapes does.
    """

    @override
    def name(self) -> str:
        return "NodeShapeValidator"

    @override
    def success_message(self) -> str:
        return "Every kernel fits on a node of the compute cluster"

    @override
    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        shapes = snapshot.resource_group.node_shapes
        if shapes is None:
            return
        oversized: list[str] = []
        for kernel in workload.placement.kernels:
            request = kernel.requested_slots.slots
            if any(_fits(request, shape) for shape in shapes):
                continue
            slots = ", ".join(
                f"{slot_name}={amount.normalize():f}"
                for slot_name, amount in sorted(request.items())
                if amount > 0
            )
            oversized.append(f"kernel {kernel.kernel_id}: {slots}")
        if oversized:
            raise NoNodeShapeFits(kernel_requests=oversized)
