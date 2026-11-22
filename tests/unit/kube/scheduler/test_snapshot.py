from __future__ import annotations

from typing import Any

from ai.backend.kube.scheduler.cycle import Resources, ShareOption
from ai.backend.kube.scheduler.snapshot import (
    bind_requested,
    build_nodes,
    build_pending_groups,
    in_flight_binds,
    live_pod_uids,
    newly_bound,
    pod_requests,
    required_levels,
    reserved_claims,
    slot_profiles,
)

GATE = [{"name": "scheduling.backend.ai/sokovan"}]
SESSION_ID = "00000000-0000-0000-0000-000000000001"
SESSION_LABELS = {
    "app.kubernetes.io/managed-by": "backendai-session-controller",
    "backend.ai/session-id": SESSION_ID,
}


def _pod(
    name: str,
    *,
    cpu: str = "1",
    node: str | None = None,
    pinned: str | None = None,
    gated: bool = False,
    phase: str = "Running",
    uid: str | None = None,
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
            "uid": uid or f"uid-{name}",
            "labels": dict(SESSION_LABELS),
            "annotations": {},
        },
        "spec": spec,
        "status": {"phase": phase},
    }


def _node(name: str, *conditions: dict[str, str], unschedulable: bool = False) -> dict[str, Any]:
    return {
        "metadata": {"name": name, "labels": {}},
        "spec": {"unschedulable": unschedulable},
        "status": {
            "allocatable": {"cpu": "8", "memory": "16Gi", "pods": "110"},
            "conditions": [{"type": "Ready", "status": "True"}, *conditions],
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


def _workload(
    kernels: int = 2,
    *,
    scheduler: str = "sokovan",
    status: dict[str, Any] | None = None,
    **spec: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "metadata": {"name": "g", "namespace": "ns", "creationTimestamp": "t"},
        "spec": {
            "sessionId": SESSION_ID,
            "schedulerName": scheduler,
            "kernels": [{"kernelId": f"k{i}"} for i in range(kernels)],
            **spec,
        },
    }
    if status is not None:
        body["status"] = status
    return body


class TestBuildPendingGroups:
    def test_only_gated_pods_of_pending_groups(self) -> None:
        pods = [_pod("a", gated=True), _pod("b", node="n1")]
        [pending] = build_pending_groups([_workload(2)], pods)
        assert [p.name for p in pending.pods] == ["a"]

    def test_the_gang_is_the_session_and_its_kernels(self) -> None:
        workload = _workload(3, priority=5)
        [pending] = build_pending_groups([workload], [_pod("a", gated=True)])
        assert (pending.namespace, pending.name) == ("ns", "g")
        assert pending.min_member == 3
        assert pending.priority == 5
        assert pending.session_id == SESSION_ID
        assert pending.created_at == "t"

    def test_pods_of_another_session_are_not_members(self) -> None:
        other = _pod("x", gated=True)
        other["metadata"]["labels"]["backend.ai/session-id"] = "other"
        unmanaged = _pod("y", gated=True)
        del unmanaged["metadata"]["labels"]["app.kubernetes.io/managed-by"]
        [pending] = build_pending_groups([_workload(1)], [_pod("a", gated=True), other, unmanaged])
        assert [p.name for p in pending.pods] == ["a"]

    def test_a_session_of_another_scheduler_is_not_placed(self) -> None:
        assert (
            build_pending_groups([_workload(1, scheduler="kueue")], [_pod("a", gated=True)]) == []
        )

    def test_a_session_being_deleted_or_terminating_is_not_placed(self) -> None:
        deleting = _workload(1)
        deleting["metadata"]["deletionTimestamp"] = "now"
        terminating = _workload(1, status={"phase": "Terminating"})
        pods = [_pod("a", gated=True)]
        assert build_pending_groups([deleting], pods) == []
        assert build_pending_groups([terminating], pods) == []

    def test_the_same_session_id_in_another_namespace_is_not_a_member(self) -> None:
        pod = _pod("a", gated=True)
        pod["metadata"]["namespace"] = "other"
        assert build_pending_groups([_workload(1)], [pod]) == []


class TestRequiredLevels:
    def test_a_single_node_session_requires_one_node(self) -> None:
        spec = _workload(2, clusterMode="single-node")["spec"]
        assert required_levels(spec) == ["kubernetes.io/hostname"]

    def test_a_multi_node_session_places_kernels_freely(self) -> None:
        assert required_levels(_workload(2, clusterMode="multi-node")["spec"]) == []

    def test_a_single_kernel_has_no_constraint(self) -> None:
        assert required_levels(_workload(1)["spec"]) == []

    def test_the_pending_group_carries_the_topology(self) -> None:
        workload = _workload(2, clusterMode="single-node")
        [pending] = build_pending_groups([workload], [_pod("a", gated=True)])
        assert pending.required_levels == ["kubernetes.io/hostname"]


class TestNewlyBound:
    def test_a_placed_session_with_every_kernel_bound(self) -> None:
        workload = _workload(2, status={"placement": {"phase": "Placed"}})
        pods = [_pod("a", node="n1"), _pod("b", node="n2")]
        assert newly_bound([workload], pods) == [(workload, 2)]

    def test_not_while_a_kernel_waits(self) -> None:
        workload = _workload(2, status={"placement": {"phase": "Placed"}})
        assert newly_bound([workload], [_pod("a", node="n1"), _pod("b", gated=True)]) == []

    def test_not_twice(self) -> None:
        workload = _workload(1, status={"placement": {"phase": "Bound"}})
        assert newly_bound([workload], [_pod("a", node="n1")]) == []


def _bind(
    pod: str, uid: str | None = None, claims: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    return {
        "metadata": {"namespace": "ns", "name": f"{pod}-x"},
        "spec": {
            "podName": pod,
            "podUid": uid or f"uid-{pod}",
            "selectedNode": "n1",
            "resourceClaimAllocations": claims or [],
        },
    }


class TestBindRequests:
    def test_failed_requests_are_not_in_flight(self) -> None:
        binds = [
            _bind("a"),
            {**_bind("b"), "status": {"phase": "Failed"}},
        ]
        assert in_flight_binds(binds) == {"uid-a": "n1"}

    def test_a_pod_with_a_bind_request_holds_its_node_and_is_not_pending(self) -> None:
        pod = _pod("waiting", gated=True)
        in_flight = {"uid-waiting": "n1"}
        [node] = build_nodes([_node("n1")], [pod], in_flight=in_flight)
        assert node.used.cpu_milli == 1000
        assert build_pending_groups([_workload(1)], [pod], in_flight) == []

    def test_an_ungated_pod_for_sokovan_is_still_pending(self) -> None:
        pod = _pod("released")
        pod["spec"]["schedulerName"] = "sokovan"
        [pending] = build_pending_groups([_workload(1)], [pod])
        assert [p.name for p in pending.pods] == ["released"]

    def test_a_placed_session_that_lost_its_bind_requests_is_placed_again(self) -> None:
        pod = _pod("waiting", gated=True)
        workload = _workload(1, status={"phase": "Pending", "placement": {"phase": "Placed"}})
        [pending] = build_pending_groups([workload], [pod], {})
        assert [p.name for p in pending.pods] == ["waiting"]


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
        [pending] = build_pending_groups([_workload(3)], pods, {"uid-b": "n1"})
        assert [p.name for p in pending.pods] == ["c"]
        assert pending.placed_members == 2
        assert pending.placed_nodes == ["n1"]

    def test_a_pod_with_a_failed_bind_request_waits_for_its_removal(self) -> None:
        pods = [_pod("a", gated=True), _pod("b", gated=True)]
        [pending] = build_pending_groups([_workload()], pods, {}, has_bind_request={"uid-a"})
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
            [_workload(1)], [pod], {}, (), [claim], slot_profiles([profile])
        )
        [share_request] = pending.pods[0].share_claims[0]
        assert share_request.driver == "gpu.x" and share_request.options[0].shares == 150

    def test_a_whole_device_request_of_a_shared_slot_asks_for_unused_devices(self) -> None:
        profiles = [
            {
                "spec": {
                    "slotName": slot,
                    "driverName": "gpu.x",
                    "deviceClassName": "shares.gpu.x",
                    "sharingMode": mode,
                }
            }
            for slot, mode in (("cuda.shares", "fraction"), ("cuda.device", "exclusive"))
        ]
        request = {"name": "r0", "exactly": {"deviceClassName": "shares.gpu.x", "count": 2}}
        claim = {
            "metadata": {"name": "p-cuda-device", "namespace": "ns"},
            "spec": {"devices": {"requests": [request]}},
        }
        pod = _pod("p", gated=True)
        pod["spec"]["resourceClaims"] = [{"name": "c", "resourceClaimName": "p-cuda-device"}]
        [pending] = build_pending_groups(
            [_workload(1)], [pod], {}, (), [claim], slot_profiles(profiles)
        )
        [share_request] = pending.pods[0].share_claims[0]
        assert share_request.options == (ShareOption(None, 2),)

    def test_a_whole_device_allocation_uses_the_full_capacity(self) -> None:
        slices = [
            _gpu_slice("n1", "n1", [{"name": "d0", "capacity": {"shares": {"value": "1650"}}}])
        ]
        claim = _foreign_claim({
            "pool": "n1",
            "driver": "gpu.x",
            "device": "d0",
            "shareID": "s1",
            "consumedCapacity": {"shares": "1650"},
        })
        [node] = build_nodes([_node("n1")], [], slices, [claim])
        assert node.share_used == {"gpu.x": {"n1/d0": 1650}}


class TestReservedClaims:
    def test_pending_and_succeeded_requests_are_reserved_by_claim(self) -> None:
        allocation: dict[str, Any] = {"devices": {"results": []}}
        binds = [
            {
                **_bind("a", claims=[{"name": "c", "allocation": allocation}]),
                "status": {"phase": phase},
            }
            for phase in ("Pending", "Succeeded", "Failed")
        ]
        expected = {"namespace": "ns", "name": "c", "allocation": allocation}
        assert reserved_claims(binds) == [expected, expected]


class TestRecreatedPod:
    """The controller recreated a Pod under the same name while the BindRequest of the Pod
    before it still exists (not yet collected, or Succeeded and kept)."""

    def _timeline(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        allocation: dict[str, Any] = {"devices": {"results": []}}
        old = _bind("a", uid="old", claims=[{"name": "c", "allocation": allocation}])
        return [_pod("a", gated=True, uid="new")], [old]

    def test_the_old_request_neither_holds_a_node_nor_reserves_claims(self) -> None:
        pods, binds = self._timeline()
        live = live_pod_uids(pods)
        in_flight = in_flight_binds(binds, live)
        assert in_flight == {}
        assert reserved_claims(binds, live) == []
        [node] = build_nodes([_node("n1")], pods, in_flight=in_flight)
        assert node.used.cpu_milli == 0

    def test_the_new_pod_is_placed_again(self) -> None:
        pods, binds = self._timeline()
        in_flight = in_flight_binds(binds, live_pod_uids(pods))
        [pending] = build_pending_groups([_workload(1)], pods, in_flight, bind_requested(binds))
        assert [p.name for p in pending.pods] == ["a"]

    def test_a_request_of_the_new_pod_holds_it(self) -> None:
        pods, binds = self._timeline()
        binds.append(_bind("a", uid="new"))
        in_flight = in_flight_binds(binds, live_pod_uids(pods))
        assert in_flight == {"new": "n1"}
        assert build_pending_groups([_workload(1)], pods, in_flight, bind_requested(binds)) == []


class TestNodeLifecycle:
    def test_a_node_to_be_recycled_takes_nothing(self) -> None:
        recycle = {"type": "nvke.nvidia.com/NeedsRecycle", "status": "True"}
        [node] = build_nodes([_node("n1", recycle)], [])
        assert not node.schedulable

    def test_a_cordoned_node_takes_nothing(self) -> None:
        [node] = build_nodes([_node("n1", unschedulable=True)], [])
        assert not node.schedulable

    def test_a_ready_node_takes_pods(self) -> None:
        recycle = {"type": "nvke.nvidia.com/NeedsRecycle", "status": "False"}
        [node] = build_nodes([_node("n1", recycle)], [])
        assert node.schedulable


class TestGroupOrderKey:
    def test_the_session_workload_creation_time_orders_a_group(self) -> None:
        workload = _workload(1)
        workload["metadata"]["creationTimestamp"] = "2026-11-22T09:00:00Z"
        [pending] = build_pending_groups([workload], [_pod("a", gated=True)])
        assert pending.created_at == "2026-11-22T09:00:00Z"


GROUP_ID = "33333333-0000-0000-0000-000000000001"


def _group_session_id(index: int) -> str:
    return f"00000000-0000-0000-0000-00000000010{index}"


def _group_workload(index: int, group: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "metadata": {"name": f"s-{index}", "namespace": "ns", "creationTimestamp": "t"},
        "spec": {
            "sessionId": _group_session_id(index),
            "kernels": [{"kernelId": "k0"}],
            **({"sessionGroup": group} if group is not None else {}),
        },
    }


def _member_pod(
    index: int, *, node: str | None = None, gated: bool = False, name: str = "main1"
) -> dict[str, Any]:
    pod = _pod(f"s-{index}-{name}", node=node, gated=gated)
    pod["metadata"]["labels"] = {
        **SESSION_LABELS,
        "backend.ai/session-id": _group_session_id(index),
        "sokovan.backend.ai/session-group": GROUP_ID,
    }
    return pod


class TestSessionGroup:
    def test_nodes_count_each_member_session_once(self) -> None:
        pods = [
            _member_pod(1, node="n1"),
            _member_pod(1, node="n1", name="sub1"),
            _member_pod(2, node="n1"),
            _member_pod(3, gated=True),
        ]
        [node] = build_nodes([_node("n1")], pods)
        assert node.group_members == {
            GROUP_ID: frozenset({_group_session_id(1), _group_session_id(2)})
        }

    def test_pending_sessions_carry_the_group_and_its_ready_members(self) -> None:
        group = {
            "id": GROUP_ID,
            "direction": "spread",
            "enforcement": "strict",
            "admission": "all_or_none",
            "memberCount": 3,
        }
        workloads = [_group_workload(i, group) for i in (1, 2, 3)]
        # s-3 has no kernel Pod yet: two of the three members are ready.
        first, second = build_pending_groups(
            workloads, [_member_pod(1, gated=True), _member_pod(2, gated=True)]
        )
        assert first.session_group is not None and first.session_group.member_count == 3
        assert (first.group_ready, second.group_ready) == (2, 2)
        assert first.unit == GROUP_ID

    def test_an_invalid_group_is_ignored(self) -> None:
        workloads = [_group_workload(1, {"id": GROUP_ID, "direction": "sideways"})]
        [pending] = build_pending_groups(workloads, [_member_pod(1, gated=True)])
        assert pending.session_group is None
