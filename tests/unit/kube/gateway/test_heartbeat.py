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
