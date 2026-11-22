from __future__ import annotations

from decimal import Decimal
from typing import Any

from ai.backend.kube.scheduler.cycle import Resources
from ai.backend.kube.scheduler.snapshot import (
    build_nodes,
    build_pending_groups,
    build_queues,
    in_flight_binds,
    pod_requests,
    reserved_claims,
    slot_profiles,
)

GATE = [{"name": "scheduling.backend.ai/sokovan"}]


def _pod(
    name: str,
    *,
    cpu: str = "1",
    node: str | None = None,
    pinned: str | None = None,
    gated: bool = False,
    phase: str = "Running",
) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "containers": [
            {"name": "kernel", "resources": {"requests": {"cpu": cpu, "memory": "1Gi"}}}
        ],
        "nodeSelector": {"kubernetes.io/hostname": pinned} if pinned else {},
    }
    if node:
        spec["nodeName"] = node
    if gated:
        spec["schedulingGates"] = GATE
    return {
        "metadata": {
            "name": name,
            "namespace": "ns",
            "labels": {"scheduling.backend.ai/queue": "q"},
            "annotations": {"scheduling.backend.ai/pod-group": "g"},
        },
        "spec": spec,
        "status": {"phase": phase},
    }


def _node(name: str) -> dict[str, Any]:
    return {
        "metadata": {"name": name, "labels": {}},
        "spec": {},
        "status": {
            "allocatable": {"cpu": "8", "memory": "16Gi", "pods": "110"},
            "conditions": [{"type": "Ready", "status": "True"}],
        },
    }


class TestPodRequests:
    def test_init_container_raises_the_floor(self) -> None:
        pod = _pod("p", cpu="500m")
        pod["spec"]["initContainers"] = [{"resources": {"requests": {"cpu": "2"}}}]
        assert pod_requests(pod) == Resources(2000, 1024**3, 1)


class TestBuildNodes:
    def test_counts_bound_and_pinned_pods_but_not_gated_or_ended(self) -> None:
        pods = [
            _pod("bound", node="n1"),
            _pod("released", pinned="n1"),
            _pod("gated", pinned="n1", gated=True),
            _pod("done", node="n1", phase="Succeeded"),
        ]
        [node] = build_nodes([_node("n1")], pods)
        assert node.used.cpu_milli == 2000

    def test_devices_come_from_slices_and_usage_from_pods_and_foreign_claims(self) -> None:
        session_pod = _pod("bound", node="n1")
        session_pod["metadata"]["annotations"]["scheduling.backend.ai/devices"] = '{"gpu.x/g": 2}'
        slot = {"slotName": {"string": "g"}}
        slices = [
            {
                "spec": {
                    "nodeName": "n1",
                    "driver": "gpu.x",
                    "pool": {"name": "n1"},
                    "devices": [{"name": f"d{i}", "attributes": slot} for i in range(4)],
                }
            }
        ]
        foreign_claim = {
            "metadata": {"name": "c", "namespace": "other", "labels": {}},
            "status": {
                "allocation": {
                    "devices": {"results": [{"pool": "n1", "driver": "gpu.x", "device": "d3"}]}
                }
            },
        }
        [node] = build_nodes([_node("n1")], [session_pod], slices, [foreign_claim])
        assert node.devices == {"gpu.x": 4, "gpu.x/g": 4}
        assert node.devices_used == {"gpu.x/g": 3}


class TestBuildQueues:
    def test_limit_from_slots_and_usage_from_running_pods(self) -> None:
        queue = {"metadata": {"name": "q"}, "spec": {"resources": {"cpu": {"limit": "3"}}}}
        states = build_queues([queue], [_pod("a", node="n1"), _pod("b", gated=True)])
        assert states["q"].limit is not None and states["q"].limit.cpu_milli == 3000
        assert states["q"].used.cpu_milli == 1000


class TestBuildPendingGroups:
    def test_only_gated_pods_of_pending_groups(self) -> None:
        group = {
            "metadata": {"name": "g", "namespace": "ns", "creationTimestamp": "t"},
            "spec": {"minMember": 2, "queue": "q"},
        }
        [pending] = build_pending_groups([group], [_pod("a", gated=True), _pod("b", node="n1")])
        assert [p.name for p in pending.pods] == ["a"]


class TestBindRequests:
    def test_failed_requests_are_not_in_flight(self) -> None:
        binds = [
            {"metadata": {"namespace": "ns"}, "spec": {"podName": "a", "selectedNode": "n1"}},
            {
                "metadata": {"namespace": "ns"},
                "spec": {"podName": "b", "selectedNode": "n1"},
                "status": {"phase": "Failed"},
            },
        ]
        assert in_flight_binds(binds) == {("ns", "a"): "n1"}

    def test_a_pod_with_a_bind_request_holds_its_node_and_is_not_pending(self) -> None:
        pod = _pod("waiting", gated=True)
        in_flight = {("ns", "waiting"): "n1"}
        [node] = build_nodes([_node("n1")], [pod], in_flight=in_flight)
        assert node.used.cpu_milli == 1000
        group = {
            "metadata": {"namespace": "ns", "name": "g"},
            "spec": {"queue": "q", "minMember": 1},
        }
        assert build_pending_groups([group], [pod], in_flight) == []

    def test_an_ungated_pod_for_sokovan_is_still_pending(self) -> None:
        pod = _pod("released")
        pod["spec"]["schedulerName"] = "sokovan"
        group = {
            "metadata": {"namespace": "ns", "name": "g"},
            "spec": {"queue": "q", "minMember": 1},
        }
        [pending] = build_pending_groups([group], [pod])
        assert [p.name for p in pending.pods] == ["released"]

    def test_a_scheduled_group_that_lost_its_bind_requests_is_placed_again(self) -> None:
        pod = _pod("waiting", gated=True)
        group = {
            "metadata": {"namespace": "ns", "name": "g"},
            "spec": {"queue": "q", "minMember": 1},
            "status": {"phase": "Scheduled"},
        }
        [pending] = build_pending_groups([group], [pod], {})
        assert [p.name for p in pending.pods] == ["waiting"]


def _group_obj(min_member: int = 2) -> dict[str, Any]:
    return {
        "metadata": {"name": "g", "namespace": "ns", "creationTimestamp": "t"},
        "spec": {"minMember": min_member, "queue": "q"},
    }


def _gpu_slice(node: str, pool: str, devices: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "spec": {"nodeName": node, "driver": "gpu.x", "pool": {"name": pool}, "devices": devices}
    }


def _foreign_claim(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "metadata": {"name": "c", "namespace": "other", "labels": {}},
        "status": {"allocation": {"devices": {"results": [result]}}},
    }


class TestGangMembers:
    def test_bound_and_in_flight_members_count_toward_min_member(self) -> None:
        pods = [_pod("a", node="n1"), _pod("b", gated=True), _pod("c", gated=True)]
        [pending] = build_pending_groups([_group_obj(3)], pods, {("ns", "b"): "n1"})
        assert [p.name for p in pending.pods] == ["c"]
        assert pending.placed_members == 2
        assert pending.placed_nodes == ["n1"]

    def test_a_pod_with_a_failed_bind_request_waits_for_its_removal(self) -> None:
        pods = [_pod("a", gated=True), _pod("b", gated=True)]
        [pending] = build_pending_groups([_group_obj()], pods, {}, has_bind_request={("ns", "a")})
        assert [p.name for p in pending.pods] == ["b"]


class TestDeviceAccounting:
    def test_a_foreign_claim_counts_on_the_node_of_its_slice(self) -> None:
        slot = {"slotName": {"string": "g"}}
        slices = [_gpu_slice("n1", "pool-a", [{"name": "d0", "attributes": slot}])]
        claim = _foreign_claim({"pool": "pool-a", "driver": "gpu.x", "device": "d0"})
        [node] = build_nodes([_node("n1")], [], slices, [claim])
        assert node.devices_used == {"gpu.x/g": 1}

    def test_extended_resources_are_counted_per_node(self) -> None:
        raw = _node("n1")
        raw["status"]["allocatable"]["nvidia.com/gpu"] = "4"
        pod = _pod("bound", node="n1")
        pod["spec"]["containers"][0]["resources"]["limits"] = {"nvidia.com/gpu": "3"}
        [node] = build_nodes([raw], [pod])
        assert node.extended == {"nvidia.com/gpu": 4}
        assert node.extended_used == {"nvidia.com/gpu": 3}

    def test_shares_come_from_slices_and_allocations(self) -> None:
        slices = [
            _gpu_slice("n1", "n1", [{"name": "d0", "capacity": {"shares": {"value": "1650"}}}])
        ]
        claim = _foreign_claim({
            "pool": "n1",
            "driver": "gpu.x",
            "device": "d0",
            "shareID": "s1",
            "consumedCapacity": {"shares": "50"},
        })
        [node] = build_nodes([_node("n1")], [], slices, [claim])
        assert node.share_capacity == {"gpu.x": {"n1/d0": 1650}}
        assert node.share_used == {"gpu.x": {"n1/d0": 50}}

    def test_share_requests_of_a_pod_are_read_from_its_claims(self) -> None:
        profile = {
            "spec": {
                "slotName": "cuda.shares",
                "driverName": "gpu.x",
                "deviceClassName": "shares.gpu.x",
                "sharingMode": "fraction",
            }
        }
        request = {
            "name": "r0",
            "exactly": {
                "deviceClassName": "shares.gpu.x",
                "count": 1,
                "capacity": {"requests": {"shares": "150"}},
            },
        }
        claim = {
            "metadata": {"name": "p-cuda-shares", "namespace": "ns"},
            "spec": {"devices": {"requests": [request]}},
        }
        pod = _pod("p", gated=True)
        pod["spec"]["resourceClaims"] = [{"name": "c", "resourceClaimName": "p-cuda-shares"}]
        [pending] = build_pending_groups(
            [_group_obj(1)], [pod], {}, (), [claim], slot_profiles([profile])
        )
        [share_request] = pending.pods[0].share_claims[0]
        assert share_request.driver == "gpu.x" and share_request.options[0].shares == 150
        assert pending.pods[0].slots == {"cuda.shares": Decimal("1.5")}


class TestQueueSlots:
    def test_device_slot_limits_and_usage(self) -> None:
        queue = {"metadata": {"name": "q"}, "spec": {"resources": {"cuda.device": {"limit": "4"}}}}
        pod = _pod("a", node="n1")
        pod["metadata"]["annotations"]["scheduling.backend.ai/devices"] = '{"gpu.x/cuda.device": 2}'
        states = build_queues([queue], [pod])
        assert states["q"].slot_limits == {"cuda.device": Decimal(4)}
        assert states["q"].slot_used == {"cuda.device": Decimal(2)}


class TestReservedClaims:
    def test_pending_and_succeeded_requests_are_reserved_by_claim(self) -> None:
        allocation: dict[str, Any] = {"devices": {"results": []}}
        binds = [
            {
                "metadata": {"namespace": "ns"},
                "spec": {
                    "podName": "a",
                    "resourceClaimAllocations": [{"name": "c", "allocation": allocation}],
                },
                "status": {"phase": phase},
            }
            for phase in ("Pending", "Succeeded", "Failed")
        ]
        expected = {"namespace": "ns", "name": "c", "allocation": allocation}
        assert reserved_claims(binds) == [expected, expected]
