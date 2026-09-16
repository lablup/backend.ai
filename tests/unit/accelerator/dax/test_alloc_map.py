import copy
from decimal import Decimal

import pytest

from ai.backend.accelerator.dax.alloc_map import DAXAllocMap
from ai.backend.agent.alloc_map import DeviceSlotInfo
from ai.backend.agent.errors.resources import InsufficientResource, InvalidResourceArgument
from ai.backend.common.types import DeviceId, SlotName, SlotTypes

SLOT = SlotName("dax.device")
DEVICE_IDS = [DeviceId("dax-0x1"), DeviceId("dax-0x2"), DeviceId("dax-0x3")]


def _make_alloc_map(device_ids: list[DeviceId], max_holders: int) -> DAXAllocMap:
    return DAXAllocMap(
        device_slots={
            device_id: DeviceSlotInfo(SlotTypes.COUNT, SLOT, Decimal(max_holders))
            for device_id in device_ids
        },
    )


def _snapshot(alloc_map: DAXAllocMap) -> dict[SlotName, dict[DeviceId, Decimal]]:
    return copy.deepcopy({slot: dict(per_dev) for slot, per_dev in alloc_map.allocations.items()})


class TestDAXAllocMapSingleHolder:
    @pytest.fixture
    def alloc_map(self) -> DAXAllocMap:
        return _make_alloc_map(DEVICE_IDS, max_holders=1)

    @pytest.mark.parametrize("count", [1, 2, 3])
    def test_grants_distinct_devices_one_unit_each(
        self, alloc_map: DAXAllocMap, count: int
    ) -> None:
        result = alloc_map.allocate({SLOT: Decimal(count)})

        granted = {dev: amount for dev, amount in result[SLOT].items() if amount > 0}
        assert len(granted) == count
        assert set(granted.values()) == {Decimal(1)}

    def test_free_restores_the_map(self, alloc_map: DAXAllocMap) -> None:
        before = _snapshot(alloc_map)
        result = alloc_map.allocate({SLOT: Decimal(2)})

        alloc_map.free(result)

        assert _snapshot(alloc_map) == before

    @pytest.mark.parametrize("amount", ["0.5", "1.5"])
    def test_fractional_request_is_rejected(self, alloc_map: DAXAllocMap, amount: str) -> None:
        before = _snapshot(alloc_map)

        with pytest.raises(InvalidResourceArgument):
            alloc_map.allocate({SLOT: Decimal(amount)})

        assert _snapshot(alloc_map) == before

    def test_more_than_free_devices_is_insufficient(self, alloc_map: DAXAllocMap) -> None:
        alloc_map.allocate({SLOT: Decimal(2)})
        before = _snapshot(alloc_map)

        with pytest.raises(InsufficientResource):
            alloc_map.allocate({SLOT: Decimal(2)})

        assert _snapshot(alloc_map) == before

    def test_zero_request_grants_nothing(self, alloc_map: DAXAllocMap) -> None:
        before = _snapshot(alloc_map)

        result = alloc_map.allocate({SLOT: Decimal(0)})

        assert all(amount == 0 for per_dev in result.values() for amount in per_dev.values())
        assert _snapshot(alloc_map) == before

    def test_apply_allocation_drops_foreign_ids(self, alloc_map: DAXAllocMap) -> None:
        alloc_map.apply_allocation({
            SLOT: {DEVICE_IDS[0]: Decimal(1), DeviceId("dax-0xdead"): Decimal(1)},
        })

        assert DeviceId("dax-0xdead") not in alloc_map.allocations[SLOT]
        assert alloc_map.allocations[SLOT][DEVICE_IDS[0]] == Decimal(1)


class TestDAXAllocMapSharedHolders:
    @pytest.fixture
    def alloc_map(self) -> DAXAllocMap:
        return _make_alloc_map(DEVICE_IDS[:1], max_holders=2)

    def test_two_kernels_share_one_device(self, alloc_map: DAXAllocMap) -> None:
        first = alloc_map.allocate({SLOT: Decimal(1)})
        second = alloc_map.allocate({SLOT: Decimal(1)})

        assert first[SLOT] == {DEVICE_IDS[0]: Decimal(1)}
        assert second[SLOT] == {DEVICE_IDS[0]: Decimal(1)}
        assert alloc_map.allocations[SLOT][DEVICE_IDS[0]] == Decimal(2)

    def test_third_holder_is_rejected(self, alloc_map: DAXAllocMap) -> None:
        alloc_map.allocate({SLOT: Decimal(1)})
        alloc_map.allocate({SLOT: Decimal(1)})
        before = _snapshot(alloc_map)

        with pytest.raises(InsufficientResource):
            alloc_map.allocate({SLOT: Decimal(1)})

        assert _snapshot(alloc_map) == before

    def test_one_kernel_never_gets_two_units_of_a_device(self, alloc_map: DAXAllocMap) -> None:
        with pytest.raises(InsufficientResource):
            alloc_map.allocate({SLOT: Decimal(2)})
