from __future__ import annotations

from typing import Any

import pytest

from ai.backend.kube.gateway.kernel_index import KernelIndex, endpoint_from_pod


def _pod(uid: str = "pod-uid-1", ip: str | None = "10.0.0.5") -> dict[str, Any]:
    return {
        "metadata": {
            "name": "s-1-main1",
            "namespace": "bai-p",
            "uid": uid,
            "labels": {"backend.ai/kernel-id": "k1", "backend.ai/session-id": "s1"},
            "ownerReferences": [{"kind": "SessionWorkload", "name": "s-1"}],
        },
        "spec": {
            "containers": [
                {
                    "name": "kernel",
                    "env": [
                        {"name": "LOCAL_USER_ID", "value": "1000"},
                        {"name": "LOCAL_GROUP_ID", "value": "1001"},
                    ],
                }
            ]
        },
        "status": {"podIP": ip, "phase": "Running"},
    }


@pytest.fixture
def index() -> KernelIndex:
    return KernelIndex()


class TestEndpointFromPod:
    def test_reads_identity_and_kernel_user(self) -> None:
        endpoint = endpoint_from_pod(_pod())
        assert endpoint is not None
        assert (endpoint.kernel_id, endpoint.session_id, endpoint.workload_name) == (
            "k1",
            "s1",
            "s-1",
        )
        assert (endpoint.uid, endpoint.gid, endpoint.pod_ip) == (1000, 1001, "10.0.0.5")

    def test_ignores_pods_without_kernel_label(self) -> None:
        pod = _pod()
        pod["metadata"]["labels"] = {}
        assert endpoint_from_pod(pod) is None


class TestKernelIndex:
    def test_tracks_latest_pod(self, index: KernelIndex) -> None:
        index.apply("ADDED", _pod(ip=None))
        index.apply("MODIFIED", _pod(ip="10.0.0.9"))
        endpoint = index.get("k1")
        assert endpoint is not None and endpoint.pod_ip == "10.0.0.9"

    def test_deleting_a_stale_pod_keeps_the_current_one(self, index: KernelIndex) -> None:
        index.apply("ADDED", _pod(uid="new"))
        index.apply("DELETED", _pod(uid="old"))
        assert index.get("k1") is not None

    def test_deleted_pod_is_forgotten(self, index: KernelIndex) -> None:
        index.apply("ADDED", _pod())
        index.apply("DELETED", _pod())
        assert index.get("k1") is None
