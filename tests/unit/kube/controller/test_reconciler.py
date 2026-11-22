from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.kube.controller.manifests import ControllerSettings
from ai.backend.kube.controller.naming import FINALIZER
from ai.backend.kube.controller.reconciler import (
    MAX_REQUEUES,
    MAX_TRANSIENT_FAILURES,
    SessionReconciler,
)
from ai.backend.kube.controller.reporter import StatusReporter
from ai.backend.kube.crd.session import SessionWorkload

KERNEL_ID = "11111111-0000-0000-0000-000000000001"


@dataclass
class Apis:
    core: AsyncMock
    net: AsyncMock
    custom: AsyncMock


@pytest.fixture
def apis(monkeypatch: pytest.MonkeyPatch) -> Apis:
    apis = Apis(core=AsyncMock(), net=AsyncMock(), custom=AsyncMock())
    apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[])
    monkeypatch.setattr(client, "CoreV1Api", lambda _api: apis.core)
    monkeypatch.setattr(client, "NetworkingV1Api", lambda _api: apis.net)
    monkeypatch.setattr(client, "CustomObjectsApi", lambda _api: apis.custom)
    return apis


@pytest.fixture
def api() -> MagicMock:
    api = MagicMock()
    api.sanitize_for_serialization.side_effect = lambda obj: obj
    return api


@pytest.fixture
def reconciler(apis: Apis, api: MagicMock, settings: ControllerSettings) -> SessionReconciler:
    return SessionReconciler(api, settings)


@pytest.fixture
def raw(workload: SessionWorkload, apis: Apis) -> dict[str, Any]:
    body = workload.to_manifest()
    body["metadata"].update(
        generation=1, resourceVersion="10", finalizers=[FINALIZER], namespace="bai-p"
    )
    apis.custom.get_namespaced_custom_object.return_value = body
    return body


def _started(raw: dict[str, Any], phase: str = "Running") -> None:
    raw["status"] = {
        "phase": phase,
        "observedGeneration": 1,
        "kernels": [{"kernelId": KERNEL_ID, "phase": phase, "podUid": "pod-uid"}],
    }


def _pod(waiting: str | None = None, **meta: Any) -> dict[str, Any]:
    state = {"waiting": {"reason": waiting}} if waiting else {"running": {}}
    return {
        "metadata": {
            "name": "s-1-main1",
            "uid": "pod-uid",
            "labels": {"backend.ai/kernel-id": KERNEL_ID},
            **meta,
        },
        "spec": {"nodeName": "n1"},
        "status": {
            "phase": "Pending" if waiting else "Running",
            "conditions": [
                {"type": "Initialized", "status": "True"},
                {"type": "Ready", "status": "False" if waiting else "True"},
            ],
            "containerStatuses": [
                {"name": "kernel", "state": state, "containerID": "containerd://cid"}
            ],
        },
    }


@pytest.fixture
def persisted_status(raw: dict[str, Any], apis: Apis) -> dict[str, Any]:
    """Status patches land in the object the next reconcile reads, as on the API server."""

    async def patch(*args: Any, **_kw: Any) -> None:
        raw["status"] = {**(raw.get("status") or {}), **args[5]["status"]}

    apis.custom.patch_namespaced_custom_object_status.side_effect = patch
    return raw


def _status_patches(apis: Apis) -> list[dict[str, Any]]:
    return [
        c.args[5]["status"]
        for c in apis.custom.patch_namespaced_custom_object_status.call_args_list
    ]


class TestFinalizer:
    async def test_added_with_a_guarded_json_patch(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        raw["metadata"]["finalizers"] = ["other/finalizer"]
        await reconciler.reconcile("bai-p", "s-1")
        call = apis.custom.patch_namespaced_custom_object.call_args
        assert call.kwargs["_content_type"] == "application/json-patch+json"
        assert call.args[5] == [
            {"op": "test", "path": "/metadata/finalizers", "value": ["other/finalizer"]},
            {"op": "add", "path": "/metadata/finalizers/-", "value": FINALIZER},
        ]

    async def test_released_by_index_once_the_pods_are_gone(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        raw["metadata"]["deletionTimestamp"] = "2026-01-01T00:00:00Z"
        raw["metadata"]["finalizers"] = ["other/finalizer", FINALIZER]
        await reconciler.reconcile("bai-p", "s-1")
        assert apis.custom.patch_namespaced_custom_object.call_args.args[5] == [
            {"op": "test", "path": "/metadata/finalizers/1", "value": FINALIZER},
            {"op": "remove", "path": "/metadata/finalizers/1"},
        ]


class TestLostNodes:
    async def test_pods_on_a_lost_node_are_force_deleted_after_the_deadline(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        raw["metadata"]["deletionTimestamp"] = "2020-01-01T00:00:00Z"
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(
            items=[_pod(deletionTimestamp="2020-01-01T00:00:00Z")]
        )
        apis.core.read_node.side_effect = ApiException(status=404)
        await reconciler.reconcile("bai-p", "s-1")
        apis.core.delete_namespaced_pod.assert_awaited_once()
        assert apis.core.delete_namespaced_pod.call_args.kwargs["grace_period_seconds"] == 0
        apis.custom.patch_namespaced_custom_object.assert_not_called()

    async def test_pods_on_a_ready_node_are_left_to_the_kubelet(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        raw["metadata"]["deletionTimestamp"] = "2020-01-01T00:00:00Z"
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(
            items=[_pod(deletionTimestamp="2020-01-01T00:00:00Z")]
        )
        apis.core.read_node.return_value = SimpleNamespace(
            status=SimpleNamespace(conditions=[SimpleNamespace(type="Ready", status="True")])
        )
        await reconciler.reconcile("bai-p", "s-1")
        apis.core.delete_namespaced_pod.assert_not_called()


class TestQuietReconcile:
    async def test_nothing_is_created_when_every_kernel_has_its_pod(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw)
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[_pod()])
        await reconciler.reconcile("bai-p", "s-1")
        apis.core.create_namespaced_pod.assert_not_called()
        apis.core.create_namespaced_service.assert_not_called()
        apis.core.read_namespaced_secret.assert_not_called()

    async def test_an_ended_session_is_left_alone(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw, "Terminated")
        await reconciler.reconcile("bai-p", "s-1")
        apis.core.list_namespaced_pod.assert_not_called()


class TestCreateFailures:
    async def test_a_missing_secret_ends_the_session_at_once(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        raw["spec"]["secretName"] = "s-1-secret"
        apis.core.read_namespaced_secret.side_effect = ApiException(status=404, reason="NotFound")
        await reconciler.reconcile("bai-p", "s-1")
        [status] = _status_patches(apis)
        assert (status["phase"], status["reason"]) == ("Error", "CreateFailed")

    async def test_a_malformed_secret_is_an_invalid_spec(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        raw["spec"]["secretName"] = "s-1-secret"
        apis.core.read_namespaced_secret.return_value = SimpleNamespace(
            data={f"kernel-{KERNEL_ID}": base64.b64encode(b"{not json").decode()}
        )
        await reconciler.reconcile("bai-p", "s-1")
        [status] = _status_patches(apis)
        assert (status["phase"], status["reason"]) == ("Error", "InvalidSpec")

    @pytest.mark.parametrize("code", [503, 403, 429])
    async def test_transient_errors_end_the_session_after_retries(
        self,
        apis: Apis,
        api: MagicMock,
        settings: ControllerSettings,
        persisted_status: dict[str, Any],
        code: int,
    ) -> None:
        apis.core.create_namespaced_service.side_effect = ApiException(status=code)
        for attempt in range(1, MAX_TRANSIENT_FAILURES):
            # A new reconciler each time: the count is in the status, not in memory.
            with pytest.raises(ApiException):
                await SessionReconciler(api, settings).reconcile("bai-p", "s-1")
            assert persisted_status["status"]["transientFailures"] == attempt
            assert persisted_status["status"]["phase"] == "Pending"
        await SessionReconciler(api, settings).reconcile("bai-p", "s-1")
        assert (persisted_status["status"]["phase"], persisted_status["status"]["reason"]) == (
            "Error",
            "CreateFailed",
        )

    async def test_a_success_resets_the_count(
        self, reconciler: SessionReconciler, persisted_status: dict[str, Any], apis: Apis
    ) -> None:
        apis.core.create_namespaced_service.side_effect = ApiException(status=503)
        with pytest.raises(ApiException):
            await reconciler.reconcile("bai-p", "s-1")
        apis.core.create_namespaced_service.side_effect = None
        await reconciler.reconcile("bai-p", "s-1")
        assert persisted_status["status"]["transientFailures"] == 0

    async def test_a_forbidden_create_is_not_a_spec_error(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        apis.core.create_namespaced_service.side_effect = ApiException(status=403)
        with pytest.raises(ApiException):
            await reconciler.reconcile("bai-p", "s-1")
        assert all(p.get("phase") != "Error" for p in _status_patches(apis))


class TestFailedPods:
    async def test_a_fatal_image_error_deletes_the_pod(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw, "Pulling")
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(
            items=[_pod("InvalidImageName")]
        )
        await reconciler.reconcile("bai-p", "s-1")
        apis.core.delete_namespaced_pod.assert_awaited_once()
        assert _status_patches(apis)[-1]["phase"] == "Error"


class TestReportedPhase:
    async def test_each_event_is_recorded_before_the_next_is_sent(
        self,
        apis: Apis,
        api: MagicMock,
        settings: ControllerSettings,
        raw: dict[str, Any],
    ) -> None:
        producer = AsyncMock()
        reconciler = SessionReconciler(api, settings, StatusReporter(producer))
        _started(raw, "Pending")
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[_pod()])
        await reconciler.reconcile("bai-p", "s-1")
        recorded = [
            p["kernels"][0]["reportedPhase"] for p in _status_patches(apis) if "kernels" in p
        ]
        assert recorded[:3] == ["Pulling", "Creating", "Running"]


class TestPodDeletedOutside:
    async def test_the_kernel_is_reported_terminated_once_its_pod_is_gone(
        self,
        apis: Apis,
        api: MagicMock,
        settings: ControllerSettings,
        raw: dict[str, Any],
    ) -> None:
        producer = AsyncMock()
        reconciler = SessionReconciler(api, settings, StatusReporter(producer))
        _started(raw)
        raw["status"]["kernels"][0]["reportedPhase"] = "Running"
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(
            items=[_pod(deletionTimestamp="2026-01-01T00:00:00Z")]
        )
        await reconciler.reconcile("bai-p", "s-1")
        assert _status_patches(apis)[-1]["phase"] == "Terminating"
        producer.anycast_and_broadcast_event.assert_not_called()

        raw["status"] = _status_patches(apis)[-1]
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[])
        await reconciler.reconcile("bai-p", "s-1")
        assert _status_patches(apis)[-1]["phase"] == "Error"
        producer.anycast_and_broadcast_event.assert_called_once()


def _requeue(raw: dict[str, Any], when: str = "2026-01-01T00:00:00Z") -> None:
    raw["metadata"]["annotations"] = {"sokovan.backend.ai/requeue": when}


def _claims(apis: Apis, *names: str) -> None:
    apis.custom.list_namespaced_custom_object.return_value = {
        "items": [{"metadata": {"name": n}} for n in names]
    }


class TestRequeue:
    async def test_a_new_requeue_deletes_pods_and_claims_without_error(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw)
        _requeue(raw)
        _claims(apis, "s-1-main1-cuda-device")
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[_pod()])
        await reconciler.reconcile("bai-p", "s-1")
        apis.core.delete_collection_namespaced_pod.assert_awaited_once()
        apis.custom.delete_collection_namespaced_custom_object.assert_awaited_once()
        apis.core.create_namespaced_pod.assert_not_called()
        [status] = _status_patches(apis)
        assert status["phase"] == "Pending" and status["reason"] == "Requeued"
        assert (status["requeueCount"], status["requeuing"]) == (1, True)
        assert status["lastRequeue"] == "2026-01-01T00:00:00Z"
        assert status["kernels"][0]["podUid"] is None

    async def test_pods_are_recreated_once_the_old_ones_are_gone(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw)
        _requeue(raw)
        raw["status"].update(lastRequeue="2026-01-01T00:00:00Z", requeueCount=1, requeuing=True)
        raw["status"]["kernels"][0]["podUid"] = None
        _claims(apis)
        await reconciler.reconcile("bai-p", "s-1")
        apis.core.create_namespaced_pod.assert_awaited_once()
        assert all(p.get("phase") != "Error" for p in _status_patches(apis))
        assert _status_patches(apis)[-1]["requeuing"] is False

    async def test_a_handled_requeue_is_not_repeated(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw)
        _requeue(raw)
        raw["status"].update(lastRequeue="2026-01-01T00:00:00Z", requeueCount=1)
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[_pod()])
        await reconciler.reconcile("bai-p", "s-1")
        apis.core.delete_collection_namespaced_pod.assert_not_called()

    async def test_too_many_requeues_end_the_session(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw)
        _requeue(raw, "2026-01-02T00:00:00Z")
        raw["status"].update(lastRequeue="2026-01-01T00:00:00Z", requeueCount=3)
        await reconciler.reconcile("bai-p", "s-1")
        status = _status_patches(apis)[-1]
        assert (status["phase"], status["reason"]) == ("Error", "RequeueLimitExceeded")

    async def test_an_admission_rejection_is_a_requeue(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw, "Pulling")
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[_rejected_pod()])
        _claims(apis)
        await reconciler.reconcile("bai-p", "s-1")
        [status] = _status_patches(apis)
        assert status["reason"] == "Requeued"
        assert (status["admissionRequeueCount"], status["requeueCount"]) == (1, 0)
        assert status["lastRequeue"] is None
        apis.core.delete_collection_namespaced_pod.assert_awaited_once()

    async def test_an_admission_rejection_after_a_kernel_started_is_an_error(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw, "Pulling")
        raw["status"]["kernels"][0]["reportedPhase"] = "Pulling"
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[_rejected_pod()])
        await reconciler.reconcile("bai-p", "s-1")
        apis.core.delete_collection_namespaced_pod.assert_not_called()
        status = _status_patches(apis)[-1]
        assert status["phase"] == "Error" and status["admissionRequeueCount"] == 0

    async def test_admission_requeues_have_their_own_limit(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw, "Pulling")
        raw["status"].update(requeueCount=MAX_REQUEUES, admissionRequeueCount=MAX_REQUEUES - 1)
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[_rejected_pod()])
        _claims(apis)
        await reconciler.reconcile("bai-p", "s-1")
        assert _status_patches(apis)[0]["admissionRequeueCount"] == MAX_REQUEUES
        raw["status"].update(admissionRequeueCount=MAX_REQUEUES, requeuing=False)
        await reconciler.reconcile("bai-p", "s-1")
        assert _status_patches(apis)[-1]["reason"] == "RequeueLimitExceeded"

    async def test_an_annotation_value_other_than_the_last_is_a_requeue(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw)
        # Earlier than the last one by the clock: still a new request.
        _requeue(raw, "2025-12-31T00:00:00Z")
        raw["status"].update(lastRequeue="2026-01-01T00:00:00Z", requeueCount=1)
        _claims(apis)
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[_pod()])
        await reconciler.reconcile("bai-p", "s-1")
        [status] = _status_patches(apis)
        assert (status["lastRequeue"], status["requeueCount"]) == ("2025-12-31T00:00:00Z", 2)

    async def test_a_pod_on_a_lost_node_does_not_hold_the_requeue(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        _started(raw)
        _requeue(raw)
        raw["status"].update(lastRequeue="2026-01-01T00:00:00Z", requeueCount=1, requeuing=True)
        _claims(apis)
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(
            items=[_pod(deletionTimestamp="2020-01-01T00:00:00Z")]
        )
        apis.core.read_node.side_effect = ApiException(status=404)
        await reconciler.reconcile("bai-p", "s-1")
        apis.core.delete_namespaced_pod.assert_awaited_once()
        assert apis.core.delete_namespaced_pod.call_args.kwargs["grace_period_seconds"] == 0
        apis.core.create_namespaced_pod.assert_not_called()


def _rejected_pod() -> dict[str, Any]:
    pod = _pod()
    pod["status"] = {"phase": "Failed", "reason": "OutOfnvidia.com/gpu"}
    return pod


def _unplaced_pod(created: datetime) -> dict[str, Any]:
    pod = _pod()
    pod["metadata"]["creationTimestamp"] = created.isoformat()
    pod["spec"] = {}
    pod["status"] = {"phase": "Pending"}
    return pod


def _placement_timeouts(producer: AsyncMock) -> list[Any]:
    return [
        c.args[0]
        for c in producer.anycast_event.call_args_list
        if c.args[0].event_name() == "session_placement_timeout"
    ]


class TestPlacementTimeout:
    @pytest.fixture
    def producer(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def reporting(
        self, apis: Apis, api: MagicMock, settings: ControllerSettings, producer: AsyncMock
    ) -> SessionReconciler:
        return SessionReconciler(api, settings, StatusReporter(producer))

    @pytest.fixture
    def pending(self, persisted_status: dict[str, Any]) -> dict[str, Any]:
        _started(persisted_status, "Pending")
        return persisted_status

    async def test_an_unplaced_session_is_reported_once_per_attempt(
        self,
        reporting: SessionReconciler,
        pending: dict[str, Any],
        apis: Apis,
        producer: AsyncMock,
    ) -> None:
        created = datetime.now(UTC) - timedelta(seconds=601)
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[_unplaced_pod(created)])
        await reporting.reconcile("bai-p", "s-1")
        [event] = _placement_timeouts(producer)
        assert str(event.session_id) == pending["spec"]["sessionId"]
        assert pending["status"]["placementTimeoutReportedAt"] is not None
        await reporting.reconcile("bai-p", "s-1")
        assert len(_placement_timeouts(producer)) == 1

    async def test_a_new_attempt_is_reported_again(
        self,
        reporting: SessionReconciler,
        pending: dict[str, Any],
        apis: Apis,
        producer: AsyncMock,
    ) -> None:
        now = datetime.now(UTC)
        pending["status"]["placementTimeoutReportedAt"] = (now - timedelta(hours=1)).isoformat()
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(
            items=[_unplaced_pod(now - timedelta(minutes=11))]
        )
        await reporting.reconcile("bai-p", "s-1")
        assert len(_placement_timeouts(producer)) == 1

    async def test_not_before_the_timeout(
        self,
        reporting: SessionReconciler,
        pending: dict[str, Any],
        apis: Apis,
        producer: AsyncMock,
    ) -> None:
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(
            items=[_unplaced_pod(datetime.now(UTC) - timedelta(seconds=30))]
        )
        await reporting.reconcile("bai-p", "s-1")
        assert _placement_timeouts(producer) == []

    async def test_a_placed_session_is_not_reported(
        self,
        reporting: SessionReconciler,
        pending: dict[str, Any],
        apis: Apis,
        producer: AsyncMock,
    ) -> None:
        pod = _unplaced_pod(datetime.now(UTC) - timedelta(hours=1))
        pod["spec"] = {"nodeName": "n1"}
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(items=[pod])
        await reporting.reconcile("bai-p", "s-1")
        assert _placement_timeouts(producer) == []

    async def test_a_session_with_a_started_kernel_is_not_reported(
        self,
        reporting: SessionReconciler,
        pending: dict[str, Any],
        apis: Apis,
        producer: AsyncMock,
    ) -> None:
        pending["status"]["kernels"][0]["reportedPhase"] = "Pulling"
        apis.core.list_namespaced_pod.return_value = SimpleNamespace(
            items=[_unplaced_pod(datetime.now(UTC) - timedelta(hours=1))]
        )
        await reporting.reconcile("bai-p", "s-1")
        assert _placement_timeouts(producer) == []


_DOMAIN_GROUP = "resource.nvidia.com"


class TestComputeDomain:
    @pytest.fixture
    def domain_session(self, raw: dict[str, Any], apis: Apis) -> dict[str, Any]:
        slots = {"cpu": "1", "mem": "1073741824", "cuda.device": "1"}
        main = {**raw["spec"]["kernels"][0], "resourceSlots": slots}
        sub = {
            **main,
            "kernelId": "11111111-0000-0000-0000-000000000002",
            "clusterRole": "sub",
            "clusterHostname": "sub1",
        }
        raw["spec"]["kernels"] = [main, sub]
        raw["spec"]["clusterSize"] = 2
        profile = {
            "metadata": {"name": "cuda-device"},
            "spec": {
                "slotName": "cuda.device",
                "sharingMode": "exclusive",
                "driverKind": "external",
                "driverName": "gpu.nvidia.com",
                "deviceClassName": "gpu.nvidia.com",
                "computeDomain": True,
            },
        }
        apis.custom.list_cluster_custom_object.return_value = {"items": [profile]}
        return raw

    async def test_created_with_the_children_and_claimed_by_every_pod(
        self, reconciler: SessionReconciler, domain_session: dict[str, Any], apis: Apis
    ) -> None:
        await reconciler.reconcile("bai-p", "s-1")
        domains = [
            c.args[4]
            for c in apis.custom.create_namespaced_custom_object.call_args_list
            if c.args[0] == _DOMAIN_GROUP
        ]
        assert [d["kind"] for d in domains] == ["ComputeDomain"]
        pods = [c.args[1] for c in apis.core.create_namespaced_pod.call_args_list]
        assert len(pods) == 2
        for pod in pods:
            assert {
                "name": "compute-domain-channel",
                "resourceClaimTemplateName": "s-1-channel",
            } in pod["spec"]["resourceClaims"]

    async def test_a_requeue_waits_until_the_domain_is_gone(
        self, reconciler: SessionReconciler, domain_session: dict[str, Any], apis: Apis
    ) -> None:
        domain_session["status"] = {
            "phase": "Pending",
            "observedGeneration": 1,
            "requeuing": True,
            "kernels": [],
        }
        _claims(apis)
        domain: dict[str, Any] = {"metadata": {"name": "s-1"}}

        async def get(group: str, *_args: Any, **_kw: Any) -> dict[str, Any]:
            if group != _DOMAIN_GROUP:
                return domain_session
            if domain.get("gone"):
                raise ApiException(status=404)
            return domain

        apis.custom.get_namespaced_custom_object.side_effect = get
        await reconciler.reconcile("bai-p", "s-1")
        apis.custom.delete_namespaced_custom_object.assert_awaited_once()
        apis.core.create_namespaced_pod.assert_not_called()

        domain["gone"] = True
        await reconciler.reconcile("bai-p", "s-1")
        assert apis.core.create_namespaced_pod.await_count == 2
