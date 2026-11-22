from __future__ import annotations

from typing import Any

import pytest

from ai.backend.kube.gateway.kernel_index import KernelIndex, endpoint_from_pod, parse_id


def _pod(
    uid: str = "pod-uid-1",
    ip: str | None = "10.0.0.5",
    *,
    namespace: str = "bai-p",
    name: str = "s-1-main1",
) -> dict[str, Any]:
    return {
        "metadata": {
            "name": name,
            "namespace": namespace,
            "uid": uid,
            "labels": {"backend.ai/kernel-id": "k1", "backend.ai/session-id": "s1"},
            "annotations": {"backend.ai/kernel-uid": "1000", "backend.ai/kernel-gid": "1001"},
            "ownerReferences": [
                {"apiVersion": "backend.ai/v1alpha1", "kind": "SessionWorkload", "name": "s-1"}
            ],
        },
        "spec": {"containers": [{"name": "kernel", "env": []}], "nodeName": "n1"},
        "status": {"podIP": ip, "phase": "Running"},
    }


def _namespace(name: str, managed: bool = True) -> dict[str, Any]:
    labels = {"app.kubernetes.io/managed-by": "backendai-manager"} if managed else {}
    return {"metadata": {"name": name, "labels": labels}}


class _Removed:
    kernel_ids: list[str]

    def __init__(self) -> None:
        self.kernel_ids = []

    def __call__(self, kernel_id: str) -> None:
        self.kernel_ids.append(kernel_id)


@pytest.fixture
def removed() -> _Removed:
    return _Removed()


@pytest.fixture
def index(removed: _Removed) -> KernelIndex:
    index = KernelIndex(on_removed=removed)
    index.replace_namespaces([_namespace("bai-p")])
    return index


class TestParseId:
    @pytest.mark.parametrize(
        ("value", "parsed"),
        [("1000", 1000), ("", None), ("-1", None), ("1e3", None), ("١٢", None), (None, None)],
        ids=["decimal", "empty", "negative", "float", "non-ascii", "missing"],
    )
    def test_only_decimal_strings_parse(self, value: object, parsed: int | None) -> None:
        assert parse_id(value) == parsed


class TestEndpointFromPod:
    def test_reads_identity_and_kernel_user_from_annotations(self) -> None:
        endpoint = endpoint_from_pod(_pod())
        assert endpoint is not None
        assert (endpoint.kernel_id, endpoint.session_id, endpoint.workload_name) == (
            "k1",
            "s1",
            "s-1",
        )
        assert (endpoint.uid, endpoint.gid, endpoint.pod_ip) == (1000, 1001, "10.0.0.5")
        assert endpoint.node_name == "n1"

    def test_an_invalid_environ_uid_is_unknown(self) -> None:
        pod = _pod()
        pod["metadata"]["annotations"] = {}
        pod["spec"]["containers"][0]["env"] = [{"name": "LOCAL_USER_ID", "value": "x"}]
        endpoint = endpoint_from_pod(pod)
        assert endpoint is not None and endpoint.uid is None

    def test_ignores_pods_without_kernel_label(self) -> None:
        pod = _pod()
        pod["metadata"]["labels"] = {}
        assert endpoint_from_pod(pod) is None

    def test_ignores_pods_not_owned_by_a_session_workload(self) -> None:
        pod = _pod()
        pod["metadata"]["ownerReferences"] = []
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

    def test_deleted_pod_is_forgotten(self, index: KernelIndex, removed: _Removed) -> None:
        index.apply("ADDED", _pod())
        index.apply("DELETED", _pod())
        assert index.get("k1") is None
        assert removed.kernel_ids == ["k1"]

    def test_a_pod_in_an_unmanaged_namespace_is_not_indexed(self, index: KernelIndex) -> None:
        index.apply("ADDED", _pod(namespace="attacker"))
        assert index.get("k1") is None

    def test_the_first_pod_keeps_a_kernel_id(self, index: KernelIndex) -> None:
        index.apply("ADDED", _pod(uid="first"))
        index.apply("ADDED", _pod(uid="second", name="other"))
        endpoint = index.get("k1")
        assert endpoint is not None and endpoint.pod_uid == "first"

    def test_relist_drops_pods_that_are_gone(self, index: KernelIndex, removed: _Removed) -> None:
        index.apply("ADDED", _pod())
        index.replace_pods([])
        assert index.get("k1") is None
        assert removed.kernel_ids == ["k1"]

    def test_a_namespace_losing_its_label_drops_its_kernels(self, index: KernelIndex) -> None:
        index.apply("ADDED", _pod())
        index.apply_namespace("MODIFIED", _namespace("bai-p", managed=False))
        assert index.get("k1") is None

    def test_a_malformed_event_does_not_raise(self, index: KernelIndex) -> None:
        index.apply("ADDED", {"metadata": {}})
        assert index.get("k1") is None
