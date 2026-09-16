import logging
from collections.abc import Mapping
from decimal import Decimal
from typing import Any, override

from ai.backend.agent.affinity_map import AffinityHint
from ai.backend.agent.alloc_map import AllocationStrategy, DiscretePropertyAllocMap
from ai.backend.agent.errors.resources import InsufficientResource, InvalidResourceArgument
from ai.backend.common.types import DeviceId, SlotName
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DAXAllocMap(DiscretePropertyAllocMap):
    """
    EVENLY allocation that grants whole units only and at most one unit per device
    to a kernel, since EVENLY alone stacks units when fewer devices are free.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, allocation_strategy=AllocationStrategy.EVENLY, **kwargs)

    @override
    def allocate(
        self,
        slots: Mapping[SlotName, Decimal],
        *,
        affinity_hint: AffinityHint | None = None,
        context_tag: str | None = None,
    ) -> Mapping[SlotName, Mapping[DeviceId, Decimal]]:
        for slot_name, requested in slots.items():
            if requested <= 0:
                continue
            if requested != requested.to_integral_value():
                raise InvalidResourceArgument(
                    f"{slot_name} accepts whole units only (requested: {requested})"
                )
            free_devices = sum(
                1
                for device_id, slot_info in self.device_slots.items()
                if slot_info.slot_name == slot_name
                and slot_info.amount - self.allocations[slot_name][device_id] >= 1
            )
            if requested > free_devices:
                raise InsufficientResource(
                    "DAXAllocMap: at most one unit per device, not enough devices with a free unit",
                    context_tag=context_tag,
                    slot_name=slot_name,
                    requested_alloc=requested,
                    total_allocatable=free_devices,
                    allocation={},
                )
        return super().allocate(slots, affinity_hint=affinity_hint, context_tag=context_tag)

    @override
    def apply_allocation(
        self,
        existing_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        known_alloc: dict[SlotName, dict[DeviceId, Decimal]] = {}
        for slot_name, per_device_alloc in existing_alloc.items():
            for device_id, alloc in per_device_alloc.items():
                if device_id not in self.device_slots:
                    log.warning("apply_allocation(): dropped unknown device {}", device_id)
                    continue
                known_alloc.setdefault(slot_name, {})[device_id] = alloc
        super().apply_allocation(known_alloc)
