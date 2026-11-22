from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.types import ResourceSlotEntry
from ai.backend.kube.crd.device import DeviceProfileSpec, SharingMode
from ai.backend.kube.gateway.heartbeat import cluster_capacity


def cluster_slots(*args: Any) -> list[ResourceSlotEntry]:
    return cluster_capacity(*args).slots


def _node(
    taints: list[dict[str, str]],
    *,
    name: str = "n1",
    cpu: str = "8",
    unschedulable: bool = False,
    conditions: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "metadata": {"name": name, "labels": {}},
        "spec": {"taints": taints, "unschedulable": unschedulable},
        "status": {
            "allocatable": {"cpu": cpu, "memory": "1Gi", "pods": "110"},
            "conditions": [{"type": "Ready", "status": "True"}, *(conditions or [])],
        },
    }


def _shares_slice() -> dict[str, Any]:
    devices = [
        {"name": f"d{i}", "capacity": {"shares": {"value": value}}}
        for i, value in enumerate(("1650", "1000"))
    ]
    return {
        "spec": {"nodeName": "n1", "driver": "gpu.x", "pool": {"name": "n1"}, "devices": devices}
    }


class TestClusterSlots:
    def test_sokovan_dedicated_nodes_count(self) -> None:
        taint = {"key": "sokovan.backend.ai/dedicated", "value": "true", "effect": "NoSchedule"}
        slots = {str(e.resource_type): e.quantity for e in cluster_slots([_node([taint])])}
        assert slots["cpu"] == "8"

    def test_other_blocking_taints_hide_a_node(self) -> None:
        taint = {"key": "maintenance", "value": "true", "effect": "NoSchedule"}
        slots = {str(e.resource_type): e.quantity for e in cluster_slots([_node([taint])])}
        assert slots["cpu"] == "0"

    def test_a_fraction_slot_reports_the_share_capacity(self) -> None:
        profile = DeviceProfileSpec(
            slot_name="cuda.shares",
            sharing_mode=SharingMode.FRACTION,
            driver_name="gpu.x",
            device_class_name="shares.gpu.x",
        )
        entries = cluster_slots([_node([])], [_shares_slice()], [profile])
        slots = {str(e.resource_type): e.quantity for e in entries}
        assert slots["cuda.shares"] == "26.5"

    def test_a_shared_slot_profile_reports_the_shared_devices(self) -> None:
        shares = DeviceProfileSpec(
            slot_name="cuda.shares",
            sharing_mode=SharingMode.FRACTION,
            driver_name="gpu.x",
            device_class_name="shares.gpu.x",
        )
        whole = shares.model_copy(
            update={
                "slot_name": "cuda.device",
                "sharing_mode": SharingMode.EXCLUSIVE,
                "shared_slot": "cuda.shares",
            }
        )
        rs = _shares_slice()
        for device in rs["spec"]["devices"]:
            device["attributes"] = {"slotName": {"string": "cuda.shares"}}
        entries = cluster_slots([_node([])], [rs], [shares, whole])
        slots = {str(e.resource_type): e.quantity for e in entries}
        assert (slots["cuda.shares"], slots["cuda.device"]) == ("26.5", "2")

    @pytest.mark.parametrize(
        "node",
        [
            _node([], unschedulable=True),
            _node([], conditions=[{"type": "nvke.nvidia.com/NeedsRecycle", "status": "True"}]),
        ],
        ids=["cordoned", "needs-recycle"],
    )
    def test_nodes_sessions_cannot_use_are_not_counted(self, node: dict[str, Any]) -> None:
        capacity = cluster_capacity([node])
        slots = {str(e.resource_type): e.quantity for e in capacity.slots}
        assert slots["cpu"] == "0"
        assert capacity.node_shapes == []

    def test_a_recycle_condition_that_is_false_counts(self) -> None:
        node = _node([], conditions=[{"type": "nvke.nvidia.com/NeedsRecycle", "status": "False"}])
        slots = {str(e.resource_type): e.quantity for e in cluster_slots([node])}
        assert slots["cpu"] == "8"


class TestNodeShapes:
    def test_distinct_node_shapes_are_reported_once(self) -> None:
        nodes = [_node([], name="a"), _node([], name="b"), _node([], name="c", cpu="16")]
        shapes = cluster_capacity(nodes).node_shapes
        assert sorted(shapes, key=lambda s: s["cpu"]) == [
            {"cpu": "16", "mem": "1073741824"},
            {"cpu": "8", "mem": "1073741824"},
        ]

    def test_a_shape_carries_the_device_slots_of_the_node(self) -> None:
        profile = DeviceProfileSpec(
            slot_name="cuda.shares",
            sharing_mode=SharingMode.FRACTION,
            driver_name="gpu.x",
            device_class_name="shares.gpu.x",
        )
        [shape] = cluster_capacity([_node([])], [_shares_slice()], [profile]).node_shapes
        assert shape["cuda.shares"] == "26.5"

    def test_at_most_256_shapes_are_reported(self) -> None:
        nodes = [_node([], name=f"n{i}", cpu=str(i + 1)) for i in range(300)]
        assert len(cluster_capacity(nodes).node_shapes) == 256


def _counters(slices: range) -> dict[str, dict[str, str]]:
    return {f"memory-slice-{i}": {"value": "1"} for i in slices}


def _mig_device(name: str, slot: str, slices: range) -> dict[str, Any]:
    return {
        "name": name,
        "attributes": {"slotName": {"string": slot}},
        "consumesCounters": [{"counterSet": "gpu-0", "counters": _counters(slices)}],
    }


def _holding(*devices: str) -> list[dict[str, Any]]:
    results = [{"driver": "gpu.x", "pool": "n1", "device": d} for d in devices]
    return [{"status": {"allocation": {"devices": {"results": results}}}}]


@pytest.fixture
def dynamic_mig_slices() -> list[dict[str, Any]]:
    """One GPU of 4 memory slices: the whole device, 1g at 0..3, 2g at 0 and 2 (split slices)."""
    whole = _mig_device("dev-0", "cuda.shares", range(4))
    whole["capacity"] = {"shares": {"value": "1000"}}
    devices = [whole]
    devices += [
        _mig_device(f"1g-{i}", "cuda.device:1g.10gb-mig", range(i, i + 1)) for i in range(4)
    ]
    devices += [_mig_device(f"2g-{i}", "cuda.device:2g.20gb-mig", range(i, i + 2)) for i in (0, 2)]
    base = {"nodeName": "n1", "driver": "gpu.x", "pool": {"name": "n1"}}
    return [
        {"spec": {**base, "sharedCounters": [{"name": "gpu-0", "counters": _counters(range(4))}]}},
        {"spec": {**base, "devices": devices}},
    ]


@pytest.fixture
def dynamic_mig_profiles() -> list[DeviceProfileSpec]:
    profiles = [
        DeviceProfileSpec(
            slot_name=slot,
            sharing_mode=SharingMode.PARTITION,
            driver_name="gpu.x",
            device_class_name="gpu.x",
        )
        for slot in ("cuda.device:1g.10gb-mig", "cuda.device:2g.20gb-mig")
    ]
    profiles.append(
        DeviceProfileSpec(
            slot_name="cuda.shares",
            sharing_mode=SharingMode.FRACTION,
            driver_name="gpu.x",
            device_class_name="gpu.x",
        )
    )
    return profiles


class TestDynamicMIGCapacity:
    @staticmethod
    def _slots(
        slices: list[dict[str, Any]],
        profiles: list[DeviceProfileSpec],
        claims: list[dict[str, Any]],
    ) -> dict[str, str]:
        capacity = cluster_capacity([_node([])], slices, profiles, claims)
        return {str(e.resource_type): e.quantity for e in capacity.slots}

    def test_an_idle_gpu_reports_each_profile_alone(
        self,
        dynamic_mig_slices: list[dict[str, Any]],
        dynamic_mig_profiles: list[DeviceProfileSpec],
    ) -> None:
        slots = self._slots(dynamic_mig_slices, dynamic_mig_profiles, [])
        assert slots["cuda.device:1g.10gb-mig"] == "4"
        assert slots["cuda.device:2g.20gb-mig"] == "2"
        assert slots["cuda.shares"] == "10"

    def test_a_held_placement_counts_and_what_overlaps_it_does_not(
        self,
        dynamic_mig_slices: list[dict[str, Any]],
        dynamic_mig_profiles: list[DeviceProfileSpec],
    ) -> None:
        slots = self._slots(dynamic_mig_slices, dynamic_mig_profiles, _holding("2g-0"))
        assert slots["cuda.device:2g.20gb-mig"] == "2"  # the held one and 2g-2
        assert slots["cuda.device:1g.10gb-mig"] == "2"  # 1g-2 and 1g-3
        assert slots["cuda.shares"] == "0"

    def test_a_gpu_in_use_whole_or_by_shares_reports_no_mig(
        self,
        dynamic_mig_slices: list[dict[str, Any]],
        dynamic_mig_profiles: list[DeviceProfileSpec],
    ) -> None:
        slots = self._slots(dynamic_mig_slices, dynamic_mig_profiles, _holding("dev-0"))
        assert slots["cuda.device:1g.10gb-mig"] == "0"
        assert slots["cuda.device:2g.20gb-mig"] == "0"
        assert slots["cuda.shares"] == "10"
