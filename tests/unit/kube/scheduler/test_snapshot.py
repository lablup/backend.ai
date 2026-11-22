from __future__ import annotations

from typing import Any

from ai.backend.kube.scheduler.cycle import Resources
from ai.backend.kube.scheduler.snapshot import (
    build_nodes,
    build_pending_groups,
    build_queues,
    in_flight_binds,
    pod_requests,
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
            "metadata": {"labels": {}},
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
