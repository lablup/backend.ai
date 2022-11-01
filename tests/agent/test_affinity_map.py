from typing import Sequence

import attr

from ai.backend.agent.affinity_map import AffinityMap
from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId, DeviceName


@attr.define(frozen=True)
class CPUDevice(AbstractComputeDevice):
    def __str__(self) -> str:
        return self.device_id

    def __repr__(self) -> str:
        # for simpler output of debug prints
        return self.device_id


@attr.define(frozen=True)
class CUDADevice(AbstractComputeDevice):
    def __str__(self) -> str:
        return self.device_id

    def __repr__(self) -> str:
        # for simpler output of debug prints
        return self.device_id


def _devid(value: Sequence[tuple[AbstractComputeDevice, int]]) -> set[tuple[DeviceId, int]]:
    return {(d.device_id, distance) for d, distance in value}


def test_affinity_map_init():
    # only a single device
    devices = [
        CPUDevice(DeviceId("a0"), "", 0, 0, 1),
    ]
    m = AffinityMap.build(devices)
    neighbor_groups = m.get_distance_ordered_neighbors(None, DeviceName("cpu"))
    assert _devid(neighbor_groups[0]) == {("a0", 0)}

    # numa_node is None
    devices = [
        CPUDevice(DeviceId("a0"), "", None, 0, 1),
        CPUDevice(DeviceId("a1"), "", None, 0, 1),
    ]
    m = AffinityMap.build(devices)
    neighbor_groups = m.get_distance_ordered_neighbors(None, DeviceName("cpu"))
    assert _devid(neighbor_groups[0]) == {("a0", 0), ("a1", 0)}

    # numa_node is -1 (cloud instances)
    devices = [
        CPUDevice(DeviceId("a0"), "", -1, 0, 1),
        CPUDevice(DeviceId("a1"), "", -1, 0, 1),
    ]
    m = AffinityMap.build(devices)
    neighbor_groups = m.get_distance_ordered_neighbors(None, DeviceName("cpu"))
    assert _devid(neighbor_groups[0]) == {("a0", 0), ("a1", 0)}


def test_affinity_map():
    devices = [
        CPUDevice(DeviceId("a0"), "", 0, 0, 1),
        CPUDevice(DeviceId("a1"), "", 0, 0, 1),
        CPUDevice(DeviceId("a2"), "", 0, 0, 1),
        CPUDevice(DeviceId("b0"), "", 1, 0, 1),
        CPUDevice(DeviceId("b1"), "", 1, 0, 1),
        CPUDevice(DeviceId("b2"), "", 1, 0, 1),
        CPUDevice(DeviceId("c0"), "", 2, 0, 1),
        CPUDevice(DeviceId("c1"), "", 2, 0, 1),
        CPUDevice(DeviceId("d0"), "", 3, 0, 1),
        CPUDevice(DeviceId("d1"), "", 3, 0, 1),
        CPUDevice(DeviceId("d2"), "", 3, 0, 1),
        CPUDevice(DeviceId("d3"), "", 3, 0, 1),
        CUDADevice(DeviceId("x0"), "", 0, 0, 1),
        CUDADevice(DeviceId("x1"), "", 1, 0, 1),
    ]
    m = AffinityMap.build(devices)

    # expecting: {d0,d1,d2,d3}
    neighbor_groups = m.get_distance_ordered_neighbors(
        None,
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {("d0", 0), ("d1", 0), ("d2", 0), ("d3", 0)}

    # expecting: {x0} or {x1}
    neighbor_groups = m.get_distance_ordered_neighbors(
        None,
        DeviceName("cuda"),
    )
    assert _devid(neighbor_groups[0]) == {("x0", 0)} or _devid(neighbor_groups[0]) == {("x1", 0)}

    # expecting: {a0,a1,a2}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-2]],  # x0
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {("a0", 0), ("a1", 0), ("a2", 0)}

    # expecting: {b0,b1,b2}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-1]],  # x1
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {("b0", 0), ("b1", 0), ("b2", 0)}

    # expecting: {a0,a1,a2},{b0,b1,b2}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-2], devices[-1]],  # x0, x1
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {("a0", 0), ("a1", 0), ("a2", 0)}
    assert _devid(neighbor_groups[1]) == {("b0", 0), ("b1", 0), ("b2", 0)}

    # expecting: {b0,b1,b2}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-1]],  # x1
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {("b0", 0), ("b1", 0), ("b2", 0)}

    # expecting: {x0},{x1}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[0], devices[1], devices[3], devices[4]],  # a0, a1, b0, b1 (two NUMA nodes)
        DeviceName("cuda"),
    )
    assert _devid(neighbor_groups[0]) == {("x0", 0)}
    assert _devid(neighbor_groups[1]) == {("x1", 0)}

    # expecting: {x0}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[0], devices[1]],  # a0, a1 (single NUMA node)
        DeviceName("cuda"),
    )
    assert _devid(neighbor_groups[0]) == {("x0", 0)}
