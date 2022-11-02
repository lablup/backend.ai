from typing import Sequence

import attrs

from ai.backend.agent.affinity_map import AffinityMap
from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId, DeviceName


@attrs.define()
class DummyDevice(AbstractComputeDevice):
    extra_prop1: str = attrs.field(default="zzz")

    def __str__(self) -> str:
        return self.device_id

    def __repr__(self) -> str:
        # for simpler output of debug prints
        return self.device_id


@attrs.define()
class CPUDevice(AbstractComputeDevice):
    extra_prop1: str = attrs.field(default="yyy")

    def __str__(self) -> str:
        return self.device_id

    def __repr__(self) -> str:
        # for simpler output of debug prints
        return self.device_id


def _devid(value: Sequence[AbstractComputeDevice]) -> set[DeviceId]:
    return {d.device_id for d in value}


def test_custom_device_class():
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


def test_affinity_map_init():
    # only a single device
    devices = [
        CPUDevice(DeviceId("a0"), "", 0, 0, 1),
    ]
    m = AffinityMap.build(devices)
    neighbor_groups = m.get_distance_ordered_neighbors(None, DeviceName("cpu"))
    assert _devid(neighbor_groups[0]) == {"a0"}

    # numa_node is None
    devices = [
        CPUDevice(DeviceId("a0"), "", None, 0, 1),
        CPUDevice(DeviceId("a1"), "", None, 0, 1),
    ]
    m = AffinityMap.build(devices)
    neighbor_groups = m.get_distance_ordered_neighbors(None, DeviceName("cpu"))
    assert _devid(neighbor_groups[0]) == {"a0", "a1"}

    # numa_node is -1 (cloud instances)
    devices = [
        CPUDevice(DeviceId("a0"), "", -1, 0, 1),
        CPUDevice(DeviceId("a1"), "", -1, 0, 1),
    ]
    m = AffinityMap.build(devices)
    neighbor_groups = m.get_distance_ordered_neighbors(None, DeviceName("cpu"))
    assert _devid(neighbor_groups[0]) == {"a0", "a1"}


def test_affinity_map():
    devices = [
        DummyDevice(DeviceId("a0"), "", 0, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("a1"), "", 0, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("a2"), "", 0, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b0"), "", 1, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b1"), "", 1, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("b2"), "", 1, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("c0"), "", 2, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("c1"), "", 2, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d0"), "", 3, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d1"), "", 3, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d2"), "", 3, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("d3"), "", 3, 0, 1, device_name=DeviceName("cpu")),
        DummyDevice(DeviceId("x0"), "", 0, 0, 1, device_name=DeviceName("cuda")),
        DummyDevice(DeviceId("x1"), "", 1, 0, 1, device_name=DeviceName("cuda")),
    ]
    m = AffinityMap.build(devices)

    # expecting: {d0,d1,d2,d3}
    neighbor_groups = m.get_distance_ordered_neighbors(
        None,
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {"d0", "d1", "d2", "d3"}

    # expecting: {x0} or {x1}
    neighbor_groups = m.get_distance_ordered_neighbors(
        None,
        DeviceName("cuda"),
    )
    assert _devid(neighbor_groups[0]) == {"x0"} or _devid(neighbor_groups[0]) == {"x1"}

    # expecting: {a0,a1,a2}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-2]],  # x0
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {"a0", "a1", "a2"}

    # expecting: {b0,b1,b2}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-1]],  # x1
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {"b0", "b1", "b2"}

    # expecting: {a0,a1,a2},{b0,b1,b2}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-2], devices[-1]],  # x0, x1
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {"a0", "a1", "a2"}
    assert _devid(neighbor_groups[1]) == {"b0", "b1", "b2"}

    # expecting: {b0,b1,b2}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[-1]],  # x1
        DeviceName("cpu"),
    )
    assert _devid(neighbor_groups[0]) == {"b0", "b1", "b2"}

    # expecting: {x0},{x1}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[0], devices[1], devices[3], devices[4]],  # a0, a1, b0, b1 (two NUMA nodes)
        DeviceName("cuda"),
    )
    assert _devid(neighbor_groups[0]) == {"x0"}
    assert _devid(neighbor_groups[1]) == {"x1"}

    # expecting: {x0}
    neighbor_groups = m.get_distance_ordered_neighbors(
        [devices[0], devices[1]],  # a0, a1 (single NUMA node)
        DeviceName("cuda"),
    )
    assert _devid(neighbor_groups[0]) == {"x0"}
