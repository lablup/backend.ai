from __future__ import annotations

from decimal import Decimal

from ai.backend.agent.data.device import DeviceAllocation
from ai.backend.common.types import DeviceId, SlotName

CUDA_DEVICE = SlotName("cuda.device")
CUDA_SHARES = SlotName("cuda.shares")


class TestDeviceAllocation:
    """Tests for transposing the agent's resource spec into per-unit amounts."""

    def test_transposes_slots_into_units(self) -> None:
        allocation = DeviceAllocation.from_device_alloc({
            CUDA_DEVICE: {DeviceId("0"): Decimal(1), DeviceId("1"): Decimal(1)},
        })
        assert [unit.device_id for unit in allocation.units] == [DeviceId("0"), DeviceId("1")]
        assert allocation.units[0].amounts == {CUDA_DEVICE: Decimal(1)}

    def test_keeps_every_slot_a_unit_is_metered_by(self) -> None:
        # A cuda device is accounted along both axes, and a plugin may read either.
        allocation = DeviceAllocation.from_device_alloc({
            CUDA_DEVICE: {DeviceId("0"): Decimal(1)},
            CUDA_SHARES: {DeviceId("0"): Decimal("0.5")},
        })
        assert len(allocation.units) == 1
        assert allocation.units[0].amounts == {
            CUDA_DEVICE: Decimal(1),
            CUDA_SHARES: Decimal("0.5"),
        }

    def test_attached_device_ids_skip_units_without_an_amount(self) -> None:
        allocation = DeviceAllocation.from_device_alloc({
            CUDA_DEVICE: {DeviceId("0"): Decimal(0), DeviceId("1"): Decimal(1)},
        })
        assert allocation.attached_device_ids == [DeviceId("1")]

    def test_attached_device_ids_keep_a_unit_metered_by_any_slot(self) -> None:
        allocation = DeviceAllocation.from_device_alloc({
            CUDA_DEVICE: {DeviceId("0"): Decimal(0)},
            CUDA_SHARES: {DeviceId("0"): Decimal("0.5")},
        })
        assert allocation.attached_device_ids == [DeviceId("0")]

    def test_an_empty_allocation_attaches_nothing(self) -> None:
        assert DeviceAllocation.from_device_alloc({}).attached_device_ids == []
