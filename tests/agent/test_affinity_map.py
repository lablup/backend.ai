from __future__ import annotations

from collections import defaultdict
from collections.abc import MutableMapping, Sequence
from decimal import Decimal
from pprint import pprint
from typing import Any

import pytest

from ai.backend.agent.affinity_map import AffinityHint, AffinityMap, AffinityPolicy
from ai.backend.agent.alloc_map import (
    AllocationStrategy,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.exception import ConfigurationError
from ai.backend.common.types import DeviceId, DeviceName, SlotName, SlotTypes


class DummyDevice(AbstractComputeDevice):
    extra_prop1: str

    def __init__(self, *args, extra_prop1: str = "zzz", **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_prop1 = extra_prop1

    def __str__(self) -> str:
        return self.device_id

    def __repr__(self) -> str:
        # for simpler output of debug prints
        return self.device_id


class CPUDevice(AbstractComputeDevice):
    extra_prop1: str

    def __init__(self, *args, extra_prop1: str = "yyy", **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_prop1 = extra_prop1

    def __str__(self) -> str:
        return self.device_id

    def __repr__(self) -> str:
        # for simpler output of debug prints
        return self.device_id


def generate_numa_cpu(
    node_id_core_seq: Sequence[tuple[int, int]],
) -> Sequence[AbstractComputeDevice]:
    devices = []
    core_idx = 0
    for node_id, count in node_id_core_seq:
        for _ in range(count):
            dev_id = DeviceId(str(core_idx))
            dev = DummyDevice(dev_id, "", 0, 1, numa_node=node_id, device_name=DeviceName("cpu"))
            devices.append(dev)
            core_idx += 1
    return devices


def _devid(value: Sequence[AbstractComputeDevice]) -> set[DeviceId]:
    """Converts the sequence of devices into the set of deivce IDs."""
    return {d.device_id for d in value}


def test_custom_device_class() -> None:
    # should be hashable
    device0 = CPUDevice(DeviceId("1"), "", 0, 0, 1)
    hash(device0)
    assert device0.device_name == "cpu"

    device1 = DummyDevice(DeviceId("x"), "", 0, 0, 1)
    hash(device1)
    assert device1.device_name == "dummy"

    device1s = DummyDevice(DeviceId("x"), "", 0, 0, 1)
    assert device1s.device_name == "dummy"

    assert device1 == device1s
    assert hash(device1) == hash(device1s)
    assert id(device1) != (device1s)

    device2 = DummyDevice(DeviceId("x"), "", 0, 0, 1, device_name=DeviceName("accel"))
    assert device2.device_name == "accel"

    assert device1 != device2
    assert hash(device1) != hash(device2)
    assert id(device1) != (device2)

    g = AffinityMap.build([device0, device1, device1s, device2])
    print([*g.edges()])
    assert g.size() == 6


def test_affinity_map_first_allocation() -> None:
    # only a single device
    devices = [
        CPUDevice(
            device_id=DeviceId("a0"), hw_location="", numa_node=0, memory_size=0, processing_units=1
        ),
    ]
    m = AffinityMap.build(devices)
    primary = m.get_device_clusters_with_lowest_distance(DeviceName("cpu"))
    assert _devid(primary[0]) == {"a0"}

    primary = m.get_device_clusters_with_lowest_distance(DeviceName("xpu"))
    assert not primary, "non-existent device name should return the empty list of primary sets"

    # numa_node is None
    devices = [
        CPUDevice(
            device_id=DeviceId("a0"),
            hw_location="",
            numa_node=None,
            memory_size=0,
            processing_units=1,
        ),
        CPUDevice(
            device_id=DeviceId("a1"),
            hw_location="",
            numa_node=None,
            memory_size=0,
            processing_units=1,
        ),
    ]
    m = AffinityMap.build(devices)
    primary = m.get_device_clusters_with_lowest_distance(DeviceName("cpu"))
    assert _devid(primary[0]) == {"a0", "a1"}

    # numa_node is -1 (cloud instances)
    devices = [
        CPUDevice(
            device_id=DeviceId("a0"),
            hw_location="",
            numa_node=-1,
            memory_size=0,
            processing_units=1,
        ),
        CPUDevice(
            device_id=DeviceId("a1"),
            hw_location="",
            numa_node=-1,
            memory_size=0,
            processing_units=1,
        ),
    ]
    m = AffinityMap.build(devices)
    primary = m.get_device_clusters_with_lowest_distance(DeviceName("cpu"))
    assert _devid(primary[0]) == {"a0", "a1"}


@pytest.mark.parametrize(
    "allocation_strategy", [AllocationStrategy.EVENLY, AllocationStrategy.FILL]
)
def test_affinity_map_prefer_larger_chunks(allocation_strategy: AllocationStrategy) -> None:
    device_init_args: dict[str, Any] = {
        "hw_location": "",
        "memory_size": 0,
        "processing_units": 1,
        "device_name": DeviceName("x"),
    }
    devices = [
        DummyDevice(DeviceId("a0"), numa_node=0, **device_init_args),
        DummyDevice(DeviceId("a1"), numa_node=0, **device_init_args),
        DummyDevice(DeviceId("a2"), numa_node=1, **device_init_args),
        DummyDevice(DeviceId("a3"), numa_node=1, **device_init_args),
    ]
    affinity_map = AffinityMap.build(devices)
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1)),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1)),
            DeviceId("a3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1)),
        },
        allocation_strategy=allocation_strategy,
    )
    primary = affinity_map.get_device_clusters_with_lowest_distance(DeviceName("x"))
    assert _devid(primary[0]) == {"a0", "a1"}
    assert _devid(primary[1]) == {"a2", "a3"}

    # The first-time allocation will happen in the first-seen neighbor component.
    affinity_hint = AffinityHint(
        None,
        affinity_map,
        AffinityPolicy.PREFER_SINGLE_NODE,
    )
    result = alloc_map.allocate(
        {SlotName("x"): Decimal("1")},
        affinity_hint=affinity_hint,
    )
    assert result[SlotName("x")][DeviceId("a0")] == 1
    assert DeviceId("a1") not in result[SlotName("x")]
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 1
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a3")] == 0

    # Test if it raises explicit configuration error when there are no matching device names.
    affinity_hint = AffinityHint(
        None,
        affinity_map,
        AffinityPolicy.PREFER_SINGLE_NODE,
    )
    with pytest.raises(ConfigurationError):
        alloc_map.allocate(
            {SlotName("y"): Decimal("1")},
            affinity_hint=affinity_hint,
        )

    # The second-time allocation with 2 devices should happen in the largest neighbor component.
    affinity_hint = AffinityHint(
        None,
        affinity_map,
        AffinityPolicy.PREFER_SINGLE_NODE,
    )
    result = alloc_map.allocate(
        {SlotName("x"): Decimal("2")},
        affinity_hint=affinity_hint,
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 1
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == 1
    assert alloc_map.allocations[SlotName("x")][DeviceId("a3")] == 1


def test_affinity_map_neighbor_devices() -> None:
    devices = [
        DummyDevice(DeviceId("a0"), "", 0, 1, numa_node=0, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("a1"), "", 0, 1, numa_node=0, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("a2"), "", 0, 1, numa_node=0, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b0"), "", 0, 1, numa_node=1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b1"), "", 0, 1, numa_node=1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b2"), "", 0, 1, numa_node=1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("c0"), "", 0, 1, numa_node=2, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("c1"), "", 0, 1, numa_node=2, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d0"), "", 0, 1, numa_node=3, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d1"), "", 0, 1, numa_node=3, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d2"), "", 0, 1, numa_node=3, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d3"), "", 0, 1, numa_node=3, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("x0"), "", 0, 1, numa_node=0, device_name=DeviceName("cuda")),
        DummyDevice(DeviceId("x1"), "", 0, 1, numa_node=1, device_name=DeviceName("cuda")),
        DummyDevice(DeviceId("x2"), "", 0, 1, numa_node=2, device_name=DeviceName("cuda")),
        DummyDevice(DeviceId("x3"), "", 0, 1, numa_node=3, device_name=DeviceName("cuda")),
    ]
    m = AffinityMap.build(devices)

    print("\n(first allocation) <cpu> cur:{d0,d1,d2,d3}")
    primary = m.get_device_clusters_with_lowest_distance(
        DeviceName("cpu"),
    )
    pprint(primary)
    assert _devid(primary[0]) == {"d0", "d1", "d2", "d3"}

    print("\n(first allocation) <cuda> cur:{x0}|{x1}")
    primary = m.get_device_clusters_with_lowest_distance(
        DeviceName("cuda"),
    )
    pprint(primary)
    assert (
        _devid(primary[0]) == {"x0"}
        or _devid(primary[0]) == {"x1"}
        or _devid(primary[0]) == {"x2"}
        or _devid(primary[0]) == {"x3"}
    )

    print("\nprev:{x0} -> cur:{a0,a1,a2},{...other-cpus}")
    primary, secondary = m.get_distance_ordered_neighbors(
        [devices[-4]],  # x0
        DeviceName("cpu"),
    )
    pprint(primary)
    pprint(secondary)
    assert _devid(primary[0]) == {"a0", "a1", "a2"}
    assert _devid(secondary) == {"b0", "b1", "b2", "c0", "c1", "d0", "d1", "d2", "d3"}

    print("\nprev:{x1} -> cur:{b0,b1,b2},{...other-cpus}")
    primary, secondary = m.get_distance_ordered_neighbors(
        [devices[-3]],  # x1
        DeviceName("cpu"),
    )
    pprint(primary)
    pprint(secondary)
    assert _devid(primary[0]) == {"b0", "b1", "b2"}
    assert _devid(secondary) == {"a0", "a1", "a2", "c0", "c1", "d0", "d1", "d2", "d3"}

    print("\nprev:{x0,x1} -> cur:{a0,a1,a2},{b0,b1,b2},{...others}")
    primary, secondary = m.get_distance_ordered_neighbors(
        [devices[-4], devices[-3]],  # x0, x1
        DeviceName("cpu"),
    )
    pprint(primary)
    pprint(secondary)
    assert _devid(primary[0]) == {"a0", "a1", "a2"}
    assert _devid(primary[1]) == {"b0", "b1", "b2"}
    assert _devid(secondary) == {"c0", "c1", "d0", "d1", "d2", "d3"}

    print("\nprev:{x0,x1,x2,x3} -> cur:{a0,a1,a2},{b0,b1,b2},{c0,c1},{...other-cpus}")
    primary, secondary = m.get_distance_ordered_neighbors(
        [devices[-3], devices[-2], devices[-1]],  # x1, x2, x3
        DeviceName("cpu"),
    )
    pprint(primary)
    pprint(secondary)
    assert _devid(primary[0]) == {"b0", "b1", "b2"}
    assert _devid(primary[1]) == {"c0", "c1"}
    assert _devid(primary[2]) == {"d0", "d1", "d2", "d3"}
    assert _devid(secondary) == {"a0", "a1", "a2"}

    print("\nprev:{a0,a1,b0,b1} -> cur:{x0},{x1},{...other-cuda-devices}")
    primary, secondary = m.get_distance_ordered_neighbors(
        [devices[0], devices[1], devices[3], devices[4]],  # a0, a1, b0, b1 (two NUMA nodes)
        DeviceName("cuda"),
    )
    pprint(primary)
    pprint(secondary)
    assert _devid(primary[0]) == {"x0"}
    assert _devid(primary[1]) == {"x1"}
    assert _devid(secondary) == {"x2", "x3"}

    print("\nprev:{a0,a1} -> cur:{x0},{...other-cuda-devices}")
    primary, secondary = m.get_distance_ordered_neighbors(
        [devices[0], devices[1]],  # a0, a1 (single NUMA node)
        DeviceName("cuda"),
    )
    assert _devid(primary[0]) == {"x0"}
    assert _devid(secondary) == {"x1", "x2", "x3"}


@pytest.mark.parametrize(
    "allocation_strategy", [AllocationStrategy.EVENLY, AllocationStrategy.FILL]
)
def test_affinity_map_secondary_allocation_simulated(
    allocation_strategy: AllocationStrategy,
) -> None:
    devices = [
        DummyDevice(DeviceId("a0"), "", 0, 1, numa_node=0, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("a1"), "", 0, 1, numa_node=0, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("a2"), "", 0, 1, numa_node=0, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b0"), "", 0, 1, numa_node=1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b1"), "", 0, 1, numa_node=1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b2"), "", 0, 1, numa_node=1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("c0"), "", 0, 1, numa_node=2, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("c1"), "", 0, 1, numa_node=2, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("c2"), "", 0, 1, numa_node=2, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d0"), "", 0, 1, numa_node=3, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d1"), "", 0, 1, numa_node=3, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d2"), "", 0, 1, numa_node=3, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("x0"), "", 0, 1, numa_node=0, device_name=DeviceName("cuda")),
        DummyDevice(DeviceId("x1"), "", 0, 1, numa_node=1, device_name=DeviceName("cuda")),
        DummyDevice(DeviceId("x2"), "", 0, 1, numa_node=2, device_name=DeviceName("cuda")),
        DummyDevice(DeviceId("x3"), "", 0, 1, numa_node=3, device_name=DeviceName("cuda")),
    ]
    affinity_map = AffinityMap.build(devices)

    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("b0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("b1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("b2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("c0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("c1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("c2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("d0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("d1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("d2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("x0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda"), Decimal(1)),
            DeviceId("x1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda"), Decimal(1)),
            DeviceId("x2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda"), Decimal(1)),
            DeviceId("x3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda"), Decimal(1)),
        },
        allocation_strategy=allocation_strategy,
    )
    primary = affinity_map.get_device_clusters_with_lowest_distance(DeviceName("cuda"))
    assert [_devid(dev_set) for dev_set in primary] == [{"x0"}, {"x1"}, {"x2"}, {"x3"}]

    primary = affinity_map.get_device_clusters_with_lowest_distance(DeviceName("cpu"))
    assert sorted([_devid(dev_set) for dev_set in primary], key=lambda s: next(iter(s))) == [
        # sorted by the alphabetical order of the first-seen item in each set
        {"a0", "a1", "a2"},
        {"b0", "b1", "b2"},
        {"c0", "c1", "c2"},
        {"d0", "d1", "d2"},
    ]

    affinity_hint = AffinityHint(
        None,
        affinity_map,
        AffinityPolicy.PREFER_SINGLE_NODE,
    )

    # Simulate the first resource slot allocation to allocate two devices from different NUMA nodes.
    alloc_map.allocations[SlotName("cuda")] = {
        DeviceId("x0"): Decimal(0),
        DeviceId("x1"): Decimal(1),
        DeviceId("x2"): Decimal(0),
        DeviceId("x3"): Decimal(1),
    }
    alloc_map.update_affinity_hint(alloc_map.allocations[SlotName("cuda")], affinity_hint)

    # The continued resource slot allocation should allocate devices from those two NUMA nodes used in the prior allocation.
    alloc_map.allocate(
        {SlotName("cpu"): Decimal("4")},
        affinity_hint=affinity_hint,
    )
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("a0")] == Decimal(0)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("a1")] == Decimal(0)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("a2")] == Decimal(0)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("b0")] == Decimal(1)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("b1")] == Decimal(1)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("b2")] == Decimal(0)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("c0")] == Decimal(0)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("c1")] == Decimal(0)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("c2")] == Decimal(0)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("d0")] == Decimal(1)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("d1")] == Decimal(1)
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("d2")] == Decimal(0)


@pytest.mark.parametrize(
    "allocation_strategy", [AllocationStrategy.EVENLY, AllocationStrategy.FILL]
)
def test_affinity_map_secondary_allocation_integrated(
    allocation_strategy: AllocationStrategy,
) -> None:
    devices = [
        DummyDevice(DeviceId("a0"), "", 0, 1, numa_node=0, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("a1"), "", 0, 1, numa_node=0, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("a2"), "", 0, 1, numa_node=0, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b0"), "", 0, 1, numa_node=1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b1"), "", 0, 1, numa_node=1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b2"), "", 0, 1, numa_node=1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("c0"), "", 0, 1, numa_node=2, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("c1"), "", 0, 1, numa_node=2, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("c2"), "", 0, 1, numa_node=2, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d0"), "", 0, 1, numa_node=3, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d1"), "", 0, 1, numa_node=3, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d2"), "", 0, 1, numa_node=3, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("x0"), "", 0, 1, numa_node=0, device_name=DeviceName("cuda")),
        DummyDevice(DeviceId("x1"), "", 0, 1, numa_node=1, device_name=DeviceName("cuda")),
        DummyDevice(DeviceId("x2"), "", 0, 1, numa_node=2, device_name=DeviceName("cuda")),
        DummyDevice(DeviceId("x3"), "", 0, 1, numa_node=3, device_name=DeviceName("cuda")),
    ]
    affinity_map = AffinityMap.build(devices)
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("b0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("b1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("b2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("c0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("c1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("c2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("d0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("d1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("d2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(1)),
            DeviceId("x0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda"), Decimal(1)),
            DeviceId("x1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda"), Decimal(1)),
            DeviceId("x2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda"), Decimal(1)),
            DeviceId("x3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda"), Decimal(1)),
        },
        allocation_strategy=allocation_strategy,
    )
    affinity_hint = AffinityHint(
        None,
        affinity_map,
        AffinityPolicy.PREFER_SINGLE_NODE,
    )
    print()

    # Do the first resource slot (cuda) allocation to allocate two devices from different NUMA nodes.
    print("[cuda]")
    alloc_map.allocate(
        {SlotName("cuda"): Decimal("2")},
        affinity_hint=affinity_hint,
    )
    per_node_cuda_alloc: MutableMapping[int, int] = defaultdict(int)
    for dev_id, alloc in alloc_map.allocations[SlotName("cuda")].items():
        if dev_id == "x0":
            per_node_cuda_alloc[0] += int(alloc)
        elif dev_id == "x1":
            per_node_cuda_alloc[1] += int(alloc)
        elif dev_id == "x2":
            per_node_cuda_alloc[2] += int(alloc)
        elif dev_id == "x3":
            per_node_cuda_alloc[3] += int(alloc)
    print("after-alloc:", alloc_map.allocations[SlotName("cuda")])
    assert sorted(per_node_cuda_alloc.values()) == [0, 0, 1, 1]
    used_numa_nodes = {node for node, count in per_node_cuda_alloc.items() if count > 0}

    # Continue resource slot (cpu) allocation should allocate devices from those two NUMA nodes used in the prior allocation.
    print("[cpu]")
    alloc_map.allocate(
        {SlotName("cpu"): Decimal("4")},
        affinity_hint=affinity_hint,
    )
    per_node_cpu_alloc: MutableMapping[int, int] = defaultdict(int)
    for dev_id, alloc in alloc_map.allocations[SlotName("cpu")].items():
        if dev_id.startswith("a"):
            per_node_cpu_alloc[0] += int(alloc)
        elif dev_id.startswith("b"):
            per_node_cpu_alloc[1] += int(alloc)
        elif dev_id.startswith("c"):
            per_node_cpu_alloc[2] += int(alloc)
        elif dev_id.startswith("d"):
            per_node_cpu_alloc[3] += int(alloc)
    print("after-alloc:", alloc_map.allocations[SlotName("cpu")])
    for node_idx, count in per_node_cpu_alloc.items():
        if node_idx in used_numa_nodes:
            assert count == 2
        else:
            assert count == 0
    assert sorted(per_node_cpu_alloc.values()) == [0, 0, 2, 2]


@pytest.mark.parametrize(
    "allocation_strategy", [AllocationStrategy.EVENLY, AllocationStrategy.FILL]
)
def test_affinity_map_secondary_allocation_with_existing_alloc(
    allocation_strategy: AllocationStrategy,
) -> None:
    devices: Sequence[AbstractComputeDevice] = [
        *generate_numa_cpu([(0, 72), (1, 72)]),
        DummyDevice(DeviceId("npu0"), "", 0, 1, numa_node=0, device_name=DeviceName("npu")),
        DummyDevice(DeviceId("npu1"), "", 0, 1, numa_node=0, device_name=DeviceName("npu")),
        DummyDevice(DeviceId("npu2"), "", 0, 1, numa_node=1, device_name=DeviceName("npu")),
        DummyDevice(DeviceId("npu3"), "", 0, 1, numa_node=1, device_name=DeviceName("npu")),
    ]
    affinity_map = AffinityMap.build(devices)
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            dev.device_id: DeviceSlotInfo(SlotTypes.COUNT, SlotName(dev.device_name), Decimal(1))
            for dev in devices
        },
        allocation_strategy=allocation_strategy,
    )
    print()

    # Simulate a prior session already allocated.
    for core_idx in range(0, 24):
        alloc_map.allocations[SlotName("cpu")][DeviceId(str(core_idx))] = Decimal(1)
    for npu_id in ("npu0", "npu1", "npu2"):
        alloc_map.allocations[SlotName("npu")][DeviceId(npu_id)] = Decimal(1)

    # Do the first resource slot (npu) allocation for the last remaining NPU device.
    affinity_hint = AffinityHint(
        None,
        affinity_map,
        AffinityPolicy.PREFER_SINGLE_NODE,
    )
    print("[npu]")
    print("current_alloc:", alloc_map.allocations[SlotName("npu")])
    new_alloc = alloc_map.allocate(
        {SlotName("npu"): Decimal("1")},
        affinity_hint=affinity_hint,
    )
    print("new_alloc:", new_alloc[SlotName("npu")])
    # The only remaining one, "npu3", is allocated.
    assert new_alloc[SlotName("npu")] == {DeviceId("npu3"): Decimal(1)}

    # Continue the next resource slot (cpu) allocation
    print("[cpu]")
    print("current_alloc:", alloc_map.allocations[SlotName("cpu")])
    new_alloc = alloc_map.allocate(
        {SlotName("cpu"): Decimal("8")},
        affinity_hint=affinity_hint,
    )
    new_alloc_per_node: MutableMapping[int, int] = defaultdict(int)
    print("new_alloc:", new_alloc[SlotName("cpu")])
    for dev_id, alloc in new_alloc[SlotName("cpu")].items():
        if 0 <= int(dev_id) < 72:
            new_alloc_per_node[0] += int(alloc)
        elif 72 <= int(dev_id) < 144:
            new_alloc_per_node[1] += int(alloc)
    # Since npu3 is in the second NUMA node, we should see the new allocations there only.
    assert new_alloc_per_node[0] == 0
    assert new_alloc_per_node[1] == 8
