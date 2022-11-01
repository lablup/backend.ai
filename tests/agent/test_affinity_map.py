from typing import Sequence

import attr

from ai.backend.agent.affinity_map import AffinityMap
from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId, DeviceName


@attr.define(frozen=True)
class DummyDevice(AbstractComputeDevice):
    def __str__(self) -> str:
        return self.device_id

    def __repr__(self) -> str:
        # for simpler output of debug prints
        return self.device_id


def _devid(value: Sequence[tuple[AbstractComputeDevice, int]]) -> set[tuple[DeviceId, int]]:
    return {(d.device_id, distance) for d, distance in value}


def test_affinity_map():
    devices = [
        DummyDevice(DeviceId("a0"), DeviceName("cpu"), "", 0, 0, 1),
        DummyDevice(DeviceId("a1"), DeviceName("cpu"), "", 0, 0, 1),
        DummyDevice(DeviceId("a2"), DeviceName("cpu"), "", 0, 0, 1),
        DummyDevice(DeviceId("b0"), DeviceName("cpu"), "", 1, 0, 1),
        DummyDevice(DeviceId("b1"), DeviceName("cpu"), "", 1, 0, 1),
        DummyDevice(DeviceId("b2"), DeviceName("cpu"), "", 1, 0, 1),
        DummyDevice(DeviceId("c0"), DeviceName("cpu"), "", 2, 0, 1),
        DummyDevice(DeviceId("c1"), DeviceName("cpu"), "", 2, 0, 1),
        DummyDevice(DeviceId("d0"), DeviceName("cpu"), "", 3, 0, 1),
        DummyDevice(DeviceId("d1"), DeviceName("cpu"), "", 3, 0, 1),
        DummyDevice(DeviceId("d2"), DeviceName("cpu"), "", 3, 0, 1),
        DummyDevice(DeviceId("d3"), DeviceName("cpu"), "", 3, 0, 1),
        DummyDevice(DeviceId("x0"), DeviceName("cuda"), "", 0, 0, 1),
        DummyDevice(DeviceId("x1"), DeviceName("cuda"), "", 1, 0, 1),
    ]
    m = AffinityMap.build(devices)

    print()
    print("expecting: {d0,d1,d2,d3}")
    neighbor_groups = m.get_distance_ordered_neighbors(
        None,
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {("d0", 0), ("d1", 0), ("d2", 0), ("d3", 0)}
    print()

    print("expecting: {x0} or {x1}")
    neighbor_groups = m.get_distance_ordered_neighbors(
        None,
        DeviceName("cuda"),
    )
    assert _devid(neighbor_groups[0]) == {("x0", 0)} or _devid(neighbor_groups[0]) == {("x1", 0)}
    print()

    print("expecting: {a0,a1,a2}")
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-2]],  # x0
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {("a0", 0), ("a1", 0), ("a2", 0)}
    print()

    print("expecting: {b0,b1,b2}")
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-1]],  # x1
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {("b0", 0), ("b1", 0), ("b2", 0)}
    print()

    print("expecting: {a0,a1,a2},{b0,b1,b2}")
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-2], devices[-1]],  # x0, x1
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {("a0", 0), ("a1", 0), ("a2", 0)}
    assert _devid(neighbor_groups[1]) == {("b0", 0), ("b1", 0), ("b2", 0)}
    print()

    print("expecting: {b0,b1,b2}")
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-1]],  # x1
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {("b0", 0), ("b1", 0), ("b2", 0)}
    print()

    print("expecting: {x0},{x1}")
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[0], devices[1], devices[3], devices[4]],  # a0, a1, b0, b1 (two NUMA nodes)
        DeviceName("cuda"),
    )
    assert _devid(neighbor_groups[0]) == {("x0", 0)}
    assert _devid(neighbor_groups[1]) == {("x1", 0)}
    print()

    print("expecting: {x0}")
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[0], devices[1]],  # a0, a1 (single NUMA node)
        DeviceName("cuda"),
    )
    assert _devid(neighbor_groups[0]) == {("x0", 0)}
