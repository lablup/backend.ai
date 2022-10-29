from collections import defaultdict

import attr

from ai.backend.agent.affinity_map import AffinityMap
from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId, DeviceName


@attr.define(frozen=True)
class DummyDevice(AbstractComputeDevice):
    pass


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

    largest_component = set()
    for device, distance in m.get_distance_ordered_neighbors(None, DeviceName("cpu")):
        largest_component.add(device.device_id)
        assert distance == 0
    assert largest_component == {"d0", "d1", "d2", "d3"}

    largest_component = set()
    for device, distance in m.get_distance_ordered_neighbors(None, DeviceName("cuda")):
        largest_component.add(device.device_id)
        assert distance == 0
    assert largest_component == {"x0"} or largest_component == {"x1"}

    distance_sets = defaultdict(set)
    for device, distance in m.get_distance_ordered_neighbors(devices[-1], DeviceName("cpu")):  # x1
        distance_sets[distance].add(device.device_id)
    assert distance_sets[0] == {"b0", "b1", "b2"}

    distance_sets = defaultdict(set)
    for device, distance in m.get_distance_ordered_neighbors(devices[6], DeviceName("cpu")):  # c0
        distance_sets[distance].add(device.device_id)
    assert distance_sets[0] == {"c0", "c1"}

    distance_sets = defaultdict(set)
    for device, distance in m.get_distance_ordered_neighbors(devices[0], DeviceName("cuda")):  # a0
        distance_sets[distance].add(device.device_id)
    assert distance_sets[0] == {"x0"}
    assert distance_sets[1] == {"x1"}
