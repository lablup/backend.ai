from __future__ import annotations

import base64
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.kube.controller.manifests import ControllerSettings
from ai.backend.kube.controller.naming import FINALIZER
from ai.backend.kube.controller.reconciler import MAX_TRANSIENT_FAILURES, SessionReconciler
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

    async def test_server_errors_end_the_session_after_retries(
        self, reconciler: SessionReconciler, raw: dict[str, Any], apis: Apis
    ) -> None:
        apis.core.create_namespaced_service.side_effect = ApiException(status=503)
        for _ in range(MAX_TRANSIENT_FAILURES - 1):
            with pytest.raises(ApiException):
                await reconciler.reconcile("bai-p", "s-1")
        assert _status_patches(apis) == []
        await reconciler.reconcile("bai-p", "s-1")
        [status] = _status_patches(apis)
        assert status["phase"] == "Error"


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
