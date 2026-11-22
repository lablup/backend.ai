from __future__ import annotations

from typing import Any

from ai.backend.kube.crd.device import DeviceProfileSpec, SharingMode
from ai.backend.kube.gateway.heartbeat import cluster_slots


def _node(taints: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "metadata": {"name": "n1", "labels": {}},
        "spec": {"taints": taints},
        "status": {
            "allocatable": {"cpu": "8", "memory": "1Gi", "pods": "110"},
            "conditions": [{"type": "Ready", "status": "True"}],
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

    def test_binder_mode_counts_only_sokovan_dedicated_nodes(self) -> None:
        taint = {"key": "sokovan.backend.ai/dedicated", "value": "true", "effect": "NoSchedule"}
        nodes = [_node([taint]), _node([])]
        slots = {
            str(e.resource_type): e.quantity for e in cluster_slots(nodes, dedicated_only=True)
        }
        assert slots["cpu"] == "8"
