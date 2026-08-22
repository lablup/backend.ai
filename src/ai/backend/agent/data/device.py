from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from ai.backend.common.types import DeviceId, SlotName


@dataclass(frozen=True)
class AllocatedDevice:
    """
    One device unit an allocation holds, and how much of it.

    A unit supplies more than one slot when it is metered along more than one axis, as a
    `cuda` device does with `cuda.device` and `cuda.shares`.
    """

    device_id: DeviceId
    amounts: Mapping[SlotName, Decimal]


@dataclass(frozen=True)
class DeviceAllocation:
    """
    The device units a compute plugin was asked to attach to a container.

    The agent keys its resource spec by slot and then by unit, which answers "how much of
    this slot went where". A plugin asks the opposite question - "which units do I attach,
    and how much of each" - so the units are transposed here once, in a stable order.
    """

    units: Sequence[AllocatedDevice]

    @classmethod
    def from_device_alloc(
        cls,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Self:
        amounts_by_unit: dict[DeviceId, dict[SlotName, Decimal]] = {}
        for slot_name, per_unit_alloc in device_alloc.items():
            for device_id, amount in per_unit_alloc.items():
                amounts_by_unit.setdefault(device_id, {})[slot_name] = amount
        return cls(
            units=[
                AllocatedDevice(device_id=device_id, amounts=amounts)
                for device_id, amounts in amounts_by_unit.items()
            ]
        )

    @property
    def attached_device_ids(self) -> list[DeviceId]:
        """The units holding a non-zero amount of any slot - the ones to attach."""
        return [
            unit.device_id
            for unit in self.units
            if any(amount > 0 for amount in unit.amounts.values())
        ]
