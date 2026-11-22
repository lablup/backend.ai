from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.kube.crd.session import SessionGroupAdmission, SessionGroupDirection
from ai.backend.kube.scheduler.cycle import (
    GroupPolicy,
    PendingGroup,
    PendingPod,
    Placement,
    Resources,
    Skip,
    SkipReason,
)
from ai.backend.kube.scheduler.runner import (
    SokovanScheduler,
    batches,
    bind_request_name,
    rolled_back,
    unplaceable_since,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)
SESSION_ID = "00000000-0000-0000-0000-000000000001"
SESSIONS = {("ns", SESSION_ID): "s-1"}
ALLOCATION = {"devices": {"results": [{"driver": "d", "pool": "p", "device": "dev-0"}]}}


def _bind(
    phase: str = "Failed", *, age: float = 0.0, session: str = "s-1", pod: str = "a"
) -> dict[str, Any]:
    return {
        "metadata": {
            "name": pod,
            "namespace": "ns",
            "resourceVersion": "7",
            "creationTimestamp": (NOW - timedelta(seconds=age)).isoformat(),
        },
        "spec": {
            "podName": pod,
            "podUid": f"uid-{pod}",
            "selectedNode": "n1",
            "session": session,
            "resourceClaimAllocations": [{"name": f"claim-{pod}", "allocation": ALLOCATION}],
        },
        "status": {"phase": phase},
    }


def _claim(pod: str, reserved: bool) -> dict[str, Any]:
    return {
        "metadata": {"name": f"claim-{pod}", "namespace": "ns"},
        "status": {
            "allocation": ALLOCATION,
            "reservedFor": [{"uid": f"uid-{pod}"}] if reserved else [{"uid": "other"}],
        },
    }


def _pod(name: str, *, node: str | None = None) -> dict[str, Any]:
    return {
        "metadata": {
            "name": name,
            "namespace": "ns",
            "uid": f"uid-{name}",
            "labels": {
                "app.kubernetes.io/managed-by": "backendai-session-controller",
                "backend.ai/session-id": SESSION_ID,
            },
        },
        "spec": {"nodeName": node} if node else {},
    }


@pytest.fixture
def scheduler() -> SokovanScheduler:
    scheduler = SokovanScheduler(MagicMock())
    scheduler._custom = MagicMock()
    scheduler._custom.patch_namespaced_custom_object_status = AsyncMock()
    scheduler._custom.delete_namespaced_custom_object = AsyncMock()
    scheduler._custom.patch_namespaced_custom_object = AsyncMock()
    scheduler._core = MagicMock()
    scheduler._core.patch_namespaced_pod = AsyncMock()
    scheduler._core.delete_namespaced_pod = AsyncMock()
    return scheduler


class TestRolledBack:
    def test_a_claim_still_held_for_the_pod_is_not_rolled_back(self) -> None:
        claims = {("ns", "claim-a"): _claim("a", reserved=True)}
        assert not rolled_back(_bind(), {}, claims)

    def test_a_claim_held_for_another_pod_does_not_count(self) -> None:
        claims = {("ns", "claim-a"): _claim("a", reserved=False)}
        assert rolled_back(_bind(), {}, claims)

    def test_a_pod_bound_as_asked_needs_no_rollback(self) -> None:
        claims = {("ns", "claim-a"): _claim("a", reserved=True)}
        pods = {("ns", "a"): _pod("a", node="n1")}
        assert rolled_back(_bind(), pods, claims)


class TestSettleFailedBinds:
    async def test_a_failed_request_is_deleted_only_after_rollback(
        self, scheduler: SokovanScheduler
    ) -> None:
        await scheduler._settle_failed_binds(
            [_bind()], [], [_claim("a", reserved=True)], NOW, SESSIONS
        )
        scheduler._custom.delete_namespaced_custom_object.assert_not_awaited()
        await scheduler._settle_failed_binds([_bind()], [], [], NOW, SESSIONS)
        scheduler._custom.delete_namespaced_custom_object.assert_awaited_once()

    async def test_a_stale_request_is_failed_with_a_precondition(
        self, scheduler: SokovanScheduler
    ) -> None:
        await scheduler._settle_failed_binds([_bind("Pending", age=120)], [], [], NOW, SESSIONS)
        body = scheduler._custom.patch_namespaced_custom_object_status.await_args.args[5]
        assert body["metadata"] == {"resourceVersion": "7"}
        assert body["status"]["phase"] == "Failed"

    async def test_an_unbound_gang_gives_up_its_other_binds(
        self, scheduler: SokovanScheduler
    ) -> None:
        binds = [_bind("Failed", pod="a"), _bind("Pending", pod="b")]
        await scheduler._settle_failed_binds(binds, [_pod("a"), _pod("b")], [], NOW, SESSIONS)
        failed = [
            call.args[4]
            for call in scheduler._custom.patch_namespaced_custom_object_status.await_args_list
        ]
        assert failed == ["b"]

    async def test_a_partly_bound_gang_keeps_its_other_binds(
        self, scheduler: SokovanScheduler
    ) -> None:
        binds = [_bind("Failed", pod="a"), _bind("Pending", pod="b")]
        pods = [_pod("a"), _pod("b"), _pod("c", node="n1")]
        await scheduler._settle_failed_binds(binds, pods, [], NOW, SESSIONS)
        scheduler._custom.patch_namespaced_custom_object_status.assert_not_awaited()


class TestUnplaceable:
    def test_a_released_pod_kube_scheduler_cannot_place(self) -> None:
        pod = _pod("a")
        pod["spec"] = {"nodeSelector": {"kubernetes.io/hostname": "n1"}}
        pod["status"] = {
            "conditions": [
                {
                    "type": "PodScheduled",
                    "status": "False",
                    "reason": "Unschedulable",
                    "lastTransitionTime": NOW.isoformat(),
                }
            ]
        }
        assert unplaceable_since(pod) == NOW
        pod["spec"]["schedulingGates"] = [{"name": "scheduling.backend.ai/sokovan"}]
        assert unplaceable_since(pod) is None

    async def test_a_stuck_release_requeues_the_gang_once(
        self, scheduler: SokovanScheduler
    ) -> None:
        pod = _pod("a")
        pod["spec"] = {"nodeSelector": {"kubernetes.io/hostname": "n1"}}
        pod["status"] = {
            "conditions": [
                {
                    "type": "PodScheduled",
                    "status": "False",
                    "reason": "Unschedulable",
                    "lastTransitionTime": (NOW - timedelta(seconds=600)).isoformat(),
                }
            ]
        }
        await scheduler._recover_unplaceable([pod, _pod("b", node="n2")], NOW, SESSIONS)
        await scheduler._recover_unplaceable([pod], NOW + timedelta(seconds=10), SESSIONS)
        scheduler._core.delete_namespaced_pod.assert_not_awaited()
        [call] = scheduler._custom.patch_namespaced_custom_object.await_args_list
        assert call.args[:5] == ("backend.ai", "v1alpha1", "ns", "sessionworkloads", "s-1")
        assert call.args[5] == {
            "metadata": {"annotations": {"sokovan.backend.ai/requeue": "2026-01-01T00:00:00Z"}}
        }


def _placement() -> Placement:
    pods = [PendingPod("ns", name, Resources(1000, 1, 1)) for name in ("a", "b")]
    group = PendingGroup("ns", "s-1", 0, "1", 2, pods, session_id=SESSION_ID)
    return Placement(group, {"a": "n1", "b": "n1"})


def _read(gated: dict[str, bool]) -> AsyncMock:
    async def read(name: str, namespace: str) -> SimpleNamespace:
        gates = [SimpleNamespace(name="scheduling.backend.ai/sokovan")] if gated[name] else []
        return SimpleNamespace(
            metadata=SimpleNamespace(deletion_timestamp=None),
            spec=SimpleNamespace(scheduling_gates=gates, node_name=None, node_selector=None),
        )

    return AsyncMock(side_effect=read)


class TestRelease:
    async def test_nothing_is_patched_unless_every_pod_still_waits(
        self, scheduler: SokovanScheduler
    ) -> None:
        scheduler._core.read_namespaced_pod = _read({"a": True, "b": False})
        result = await scheduler._release(_placement())
        assert isinstance(result, Skip) and result.reason == SkipReason.WAITING_FOR_PODS
        scheduler._core.patch_namespaced_pod.assert_not_awaited()

    async def test_every_pod_is_pinned_and_ungated(self, scheduler: SokovanScheduler) -> None:
        scheduler._core.read_namespaced_pod = _read({"a": True, "b": True})
        result = await scheduler._release(_placement())
        assert isinstance(result, Placement)
        assert scheduler._core.patch_namespaced_pod.await_count == 2


class TestStaleGang:
    async def test_a_partly_placed_gang_is_requeued_after_the_timeout(
        self, scheduler: SokovanScheduler
    ) -> None:
        group = replace(_placement().group, placed_members=1)
        skip = Skip(group, SkipReason.UNSCHEDULABLE, "no fit")
        await scheduler._tear_down_stale_gangs([skip], NOW)
        scheduler._custom.patch_namespaced_custom_object.assert_not_awaited()
        await scheduler._tear_down_stale_gangs([skip], NOW + timedelta(seconds=301))
        [call] = scheduler._custom.patch_namespaced_custom_object.await_args_list
        assert call.args[3:5] == ("sessionworkloads", "s-1")
        scheduler._core.delete_namespaced_pod.assert_not_awaited()


class TestBindRequestName:
    def test_a_recreated_pod_gets_its_own_request(self) -> None:
        old, new = _pod("a"), _pod("a")
        new["metadata"]["uid"] = "uid-b"
        assert bind_request_name(old) != bind_request_name(new)

    def test_a_long_pod_name_stays_a_valid_name(self) -> None:
        pod = _pod("p" * 253)
        assert len(bind_request_name(pod)) == 253

    async def test_a_request_written_already_is_not_an_error(
        self, scheduler: SokovanScheduler
    ) -> None:
        scheduler._custom.create_namespaced_custom_object = AsyncMock(
            side_effect=ApiException(status=409)
        )
        await scheduler._create_bind_request(_pod("a"), "n1", "s-1", [])
        [call] = scheduler._custom.create_namespaced_custom_object.await_args_list
        assert call.args[4]["spec"]["podUid"] == "uid-a"
        assert call.args[4]["spec"]["session"] == "s-1"


def _placement_writes(scheduler: SokovanScheduler) -> list[tuple[Any, ...]]:
    return [
        (*call.args[:5], call.args[5]["status"]["placement"])
        for call in scheduler._custom.patch_namespaced_custom_object_status.await_args_list
    ]


def _workload(placement: dict[str, Any] | None = None) -> dict[str, Any]:
    status = {"phase": "Pending", **({"placement": placement} if placement else {})}
    return {
        "metadata": {"name": "s-1", "namespace": "ns"},
        "spec": {"sessionId": SESSION_ID, "kernels": [{"kernelId": "k0"}, {"kernelId": "k1"}]},
        "status": status,
    }


class TestPlacementStatus:
    async def test_a_placement_is_written_to_the_session_workload_status(
        self, scheduler: SokovanScheduler
    ) -> None:
        await scheduler._report(_placement(), _workload())
        [(group, _version, ns, plural, name, placement)] = _placement_writes(scheduler)
        assert (group, ns, plural, name) == ("backend.ai", "ns", "sessionworkloads", "s-1")
        assert placement["phase"] == "Placed" and placement["scheduled"] == 2
        assert placement["lastAttempt"] is not None
        # Sent as null: a merge patch clears the reason of an earlier skip.
        assert placement["reason"] is None and placement["message"] is None

    async def test_the_patch_carries_only_the_placement(self, scheduler: SokovanScheduler) -> None:
        await scheduler._report(_placement(), _workload())
        [call] = scheduler._custom.patch_namespaced_custom_object_status.await_args_list
        assert list(call.args[5]) == ["status"] and list(call.args[5]["status"]) == ["placement"]
        assert call.kwargs["_content_type"] == "application/merge-patch+json"

    @pytest.mark.parametrize(
        ("reason", "phase"),
        [
            (SkipReason.UNSCHEDULABLE, "Unschedulable"),
            (SkipReason.UNSUPPORTED, "Unschedulable"),
            (SkipReason.RESERVED, "Pending"),
            (SkipReason.WAITING_FOR_PODS, "Pending"),
        ],
    )
    async def test_a_skip_records_its_reason(
        self, scheduler: SokovanScheduler, reason: SkipReason, phase: str
    ) -> None:
        await scheduler._report(Skip(_placement().group, reason, "why"), _workload())
        [(*_, placement)] = _placement_writes(scheduler)
        assert (placement["phase"], placement["reason"], placement["message"]) == (
            phase,
            str(reason),
            "why",
        )

    async def test_an_unchanged_skip_is_not_written_again(
        self, scheduler: SokovanScheduler
    ) -> None:
        current = _workload({"phase": "Unschedulable", "reason": "Unschedulable"})
        skip = Skip(_placement().group, SkipReason.UNSCHEDULABLE, "no fit")
        await scheduler._report(skip, current)
        scheduler._custom.patch_namespaced_custom_object_status.assert_not_awaited()

    async def test_a_placed_session_whose_kernels_are_bound_becomes_bound(
        self, scheduler: SokovanScheduler
    ) -> None:
        workload = _workload({"phase": "Placed", "lastAttempt": "t"})
        pods = [_pod("a", node="n1"), _pod("b", node="n1")]
        await scheduler._report_bound([workload], pods)
        [(*_, name, placement)] = _placement_writes(scheduler)
        assert name == "s-1"
        assert (placement["phase"], placement["scheduled"], placement["lastAttempt"]) == (
            "Bound",
            2,
            "t",
        )

    async def test_a_deleted_session_workload_is_not_an_error(
        self, scheduler: SokovanScheduler
    ) -> None:
        scheduler._custom.patch_namespaced_custom_object_status.side_effect = ApiException(
            status=404
        )
        await scheduler._report(_placement(), _workload())


def _kernel_pod(name: str) -> dict[str, Any]:
    pod = _pod(name)
    pod["spec"] = {
        "schedulingGates": [{"name": "scheduling.backend.ai/sokovan"}],
        "containers": [{"name": "kernel", "resources": {"requests": {"cpu": "1"}}}],
    }
    pod["status"] = {"phase": "Pending"}
    return pod


def _ready_node(name: str) -> dict[str, Any]:
    return {
        "metadata": {"name": name, "labels": {"kubernetes.io/hostname": name}},
        "spec": {},
        "status": {
            "allocatable": {"cpu": "4", "memory": "8Gi", "pods": "110"},
            "conditions": [{"type": "Ready", "status": "True"}],
        },
    }


class TestCycle:
    @pytest.fixture
    def listed(self, scheduler: SokovanScheduler) -> dict[str, list[dict[str, Any]]]:
        """What the API server lists, by plural; the scheduler reads it once per cycle."""
        objects: dict[str, list[dict[str, Any]]] = {
            "sessionworkloads": [_workload()],
            "resourceslices": [],
            "resourceclaims": [],
            "bindrequests": [],
            "deviceprofiles": [],
        }
        pods = [_kernel_pod("a"), _kernel_pod("b")]

        async def list_custom(_group: str, _version: str, plural: str) -> dict[str, Any]:
            return {"items": objects[plural]}

        scheduler._api.sanitize_for_serialization.side_effect = lambda obj: obj
        scheduler._custom.list_cluster_custom_object = AsyncMock(side_effect=list_custom)
        scheduler._core.list_node = AsyncMock(
            return_value=SimpleNamespace(items=[_ready_node("n1")])
        )
        scheduler._core.list_pod_for_all_namespaces = AsyncMock(
            return_value=SimpleNamespace(items=pods)
        )
        scheduler._core.read_namespaced_pod = _read({"a": True, "b": True})
        return objects

    async def test_the_kernels_of_a_session_workload_are_placed_together(
        self, scheduler: SokovanScheduler, listed: dict[str, list[dict[str, Any]]]
    ) -> None:
        await scheduler.cycle()
        released = {c.args[0] for c in scheduler._core.patch_namespaced_pod.await_args_list}
        assert released == {"a", "b"}
        [(*_, name, placement)] = _placement_writes(scheduler)
        assert (name, placement["phase"], placement["scheduled"]) == ("s-1", "Placed", 2)

    async def test_a_session_with_a_kernel_pod_missing_waits(
        self, scheduler: SokovanScheduler, listed: dict[str, list[dict[str, Any]]]
    ) -> None:
        listed["sessionworkloads"][0]["spec"]["kernels"].append({"kernelId": "k2"})
        await scheduler.cycle()
        scheduler._core.patch_namespaced_pod.assert_not_awaited()
        [(*_, placement)] = _placement_writes(scheduler)
        assert (placement["phase"], placement["reason"]) == ("Pending", "WaitingForPods")


GROUP = GroupPolicy(
    id="33333333-0000-0000-0000-000000000001",
    direction=SessionGroupDirection.SPREAD,
    admission=SessionGroupAdmission.ALL_OR_NONE,
    member_count=2,
)


def _member_placement(name: str, pod: str) -> Placement:
    group = PendingGroup(
        "ns",
        name,
        0,
        "1",
        1,
        [PendingPod("ns", pod, Resources(1000, 1, 1))],
        session_id=name,
        session_group=GROUP,
        group_ready=2,
    )
    return Placement(group, {pod: "n1"})


class TestAllOrNoneStart:
    @pytest.fixture
    def members(self) -> list[Placement | Skip]:
        return [_member_placement("s-1", "a"), _member_placement("s-2", "b")]

    def test_the_members_of_a_group_form_one_batch(self, members: list[Placement | Skip]) -> None:
        single = _placement()
        assert batches([members[0], single, members[1]]) == [
            [members[0], members[1]],
            [single],
        ]

    async def test_no_member_is_released_unless_every_pod_still_waits(
        self, scheduler: SokovanScheduler, members: list[Placement | Skip]
    ) -> None:
        scheduler._core.read_namespaced_pod = _read({"a": True, "b": False})
        results = await scheduler._release_all(members)
        assert [r.reason for r in results if isinstance(r, Skip)] == [
            SkipReason.WAITING_FOR_PODS
        ] * 2
        scheduler._core.patch_namespaced_pod.assert_not_awaited()

    async def test_every_member_is_released_together(
        self, scheduler: SokovanScheduler, members: list[Placement | Skip]
    ) -> None:
        scheduler._core.read_namespaced_pod = _read({"a": True, "b": True})
        results = await scheduler._release_all(members)
        assert all(isinstance(r, Placement) for r in results)
        assert scheduler._core.patch_namespaced_pod.await_count == 2

    async def test_a_group_that_does_not_fit_is_reported_unschedulable(
        self, scheduler: SokovanScheduler, members: list[Placement | Skip]
    ) -> None:
        skip = Skip(members[0].group, SkipReason.GROUP_DOES_NOT_FIT, "no fit")
        await scheduler._report(skip, _workload())
        [(*_, placement)] = _placement_writes(scheduler)
        assert (placement["phase"], placement["reason"]) == ("Unschedulable", "GroupDoesNotFit")
