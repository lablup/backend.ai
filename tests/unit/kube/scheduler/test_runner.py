from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.kube.scheduler.cycle import (
    PendingGroup,
    PendingPod,
    Placement,
    Resources,
    Skip,
    SkipReason,
)
from ai.backend.kube.scheduler.runner import (
    SokovanScheduler,
    bind_request_name,
    rolled_back,
    unplaceable_since,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)
ALLOCATION = {"devices": {"results": [{"driver": "d", "pool": "p", "device": "dev-0"}]}}


def _bind(
    phase: str = "Failed", *, age: float = 0.0, group: str = "g", pod: str = "a"
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
            "podGroup": group,
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
            "annotations": {"scheduling.backend.ai/pod-group": "g"},
            "ownerReferences": [
                {"apiVersion": "backend.ai/v1alpha1", "kind": "SessionWorkload", "name": "s-1"}
            ],
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
        await scheduler._settle_failed_binds([_bind()], [], [_claim("a", reserved=True)], NOW)
        scheduler._custom.delete_namespaced_custom_object.assert_not_awaited()
        await scheduler._settle_failed_binds([_bind()], [], [], NOW)
        scheduler._custom.delete_namespaced_custom_object.assert_awaited_once()

    async def test_a_stale_request_is_failed_with_a_precondition(
        self, scheduler: SokovanScheduler
    ) -> None:
        await scheduler._settle_failed_binds([_bind("Pending", age=120)], [], [], NOW)
        body = scheduler._custom.patch_namespaced_custom_object_status.await_args.args[5]
        assert body["metadata"] == {"resourceVersion": "7"}
        assert body["status"]["phase"] == "Failed"

    async def test_an_unbound_gang_gives_up_its_other_binds(
        self, scheduler: SokovanScheduler
    ) -> None:
        binds = [_bind("Failed", pod="a"), _bind("Pending", pod="b")]
        await scheduler._settle_failed_binds(binds, [_pod("a"), _pod("b")], [], NOW)
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
        await scheduler._settle_failed_binds(binds, pods, [], NOW)
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
        await scheduler._recover_unplaceable([pod, _pod("b", node="n2")], NOW)
        await scheduler._recover_unplaceable([pod], NOW + timedelta(seconds=10))
        scheduler._core.delete_namespaced_pod.assert_not_awaited()
        [call] = scheduler._custom.patch_namespaced_custom_object.await_args_list
        assert call.args[:5] == ("backend.ai", "v1alpha1", "ns", "sessionworkloads", "s-1")
        assert call.args[5] == {
            "metadata": {"annotations": {"sokovan.backend.ai/requeue": "2026-01-01T00:00:00Z"}}
        }


def _placement() -> Placement:
    pods = [PendingPod("ns", name, Resources(1000, 1, 1)) for name in ("a", "b")]
    group = PendingGroup("ns", "g", 0, "1", 2, pods)
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
        pods = [_pod("a", node="n1"), _pod("b")]
        await scheduler._tear_down_stale_gangs([skip], pods, NOW)
        scheduler._custom.patch_namespaced_custom_object.assert_not_awaited()
        await scheduler._tear_down_stale_gangs([skip], pods, NOW + timedelta(seconds=301))
        scheduler._custom.patch_namespaced_custom_object.assert_awaited_once()
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
        await scheduler._create_bind_request(_pod("a"), "n1", "g", [])
        [call] = scheduler._custom.create_namespaced_custom_object.await_args_list
        assert call.args[4]["spec"]["podUid"] == "uid-a"
