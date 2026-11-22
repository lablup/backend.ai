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
    kernel_id: str = "k1",
    owner_uid: str = "sw-uid-1",
) -> dict[str, Any]:
    return {
        "metadata": {
            "name": name,
            "namespace": namespace,
            "uid": uid,
            "labels": {"backend.ai/kernel-id": kernel_id, "backend.ai/session-id": "s1"},
            "annotations": {"backend.ai/kernel-uid": "1000", "backend.ai/kernel-gid": "1001"},
            "ownerReferences": [
                {
                    "apiVersion": "backend.ai/v1alpha1",
                    "kind": "SessionWorkload",
                    "name": "s-1",
                    "uid": owner_uid,
                }
            ],
        },
        "spec": {"containers": [{"name": "kernel", "env": []}], "nodeName": "n1"},
        "status": {"podIP": ip, "phase": "Running"},
    }


def _workload(
    uid: str = "sw-uid-1", namespace: str = "bai-p", kernel_ids: tuple[str, ...] = ("k1",)
) -> dict[str, Any]:
    return {
        "metadata": {"name": "s-1", "namespace": namespace, "uid": uid},
        "spec": {"sessionId": "s1", "kernels": [{"kernelId": k} for k in kernel_ids]},
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
    index.replace_workloads([_workload()])
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
        assert endpoint.workload_uid == "sw-uid-1"
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

    def test_an_owner_reference_to_another_workload_is_not_indexed(
        self, index: KernelIndex
    ) -> None:
        index.apply("ADDED", _pod(owner_uid="forged"))
        assert index.get("k1") is None

    def test_a_kernel_id_the_workload_does_not_declare_is_not_indexed(
        self, index: KernelIndex
    ) -> None:
        index.apply("ADDED", _pod(kernel_id="k9"))
        assert index.get("k9") is None

    def test_a_workload_in_another_namespace_does_not_vouch(self, index: KernelIndex) -> None:
        index.replace_namespaces([_namespace("bai-p"), _namespace("bai-q")])
        index.apply("ADDED", _pod(namespace="bai-q"))
        assert index.get("k1") is None

    def test_a_pod_seen_before_its_workload_is_indexed_once_it_arrives(self) -> None:
        index = KernelIndex()
        index.replace_namespaces([_namespace("bai-p")])
        index.apply("ADDED", _pod())
        assert index.get("k1") is None
        index.apply_workload("ADDED", _workload())
        assert index.get("k1") is not None

    def test_a_deleted_workload_drops_its_kernels(
        self, index: KernelIndex, removed: _Removed
    ) -> None:
        index.apply("ADDED", _pod())
        index.apply_workload("DELETED", _workload())
        assert index.get("k1") is None
        assert removed.kernel_ids == ["k1"]

    def test_the_next_pod_takes_over_when_the_first_is_deleted(self, index: KernelIndex) -> None:
        index.apply("ADDED", _pod(uid="first"))
        index.apply("ADDED", _pod(uid="second", name="other"))
        index.apply("DELETED", _pod(uid="first"))
        endpoint = index.get("k1")
        assert endpoint is not None and endpoint.pod_uid == "second"


class TestKernelIndexCost:
    def test_a_relist_and_its_added_events_resolve_each_kernel_a_bounded_number_of_times(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        count = 2000
        kernel_ids = tuple(f"k{i}" for i in range(count))
        pods = [_pod(uid=f"p{i}", name=f"p{i}", kernel_id=k) for i, k in enumerate(kernel_ids)]
        index = KernelIndex()
        index.replace_namespaces([_namespace("bai-p")])
        index.replace_workloads([_workload(kernel_ids=kernel_ids)])
        checks = 0
        valid = KernelIndex._valid

        def counting(self: KernelIndex, endpoint: Any) -> bool:
            nonlocal checks
            checks += 1
            return valid(self, endpoint)

        monkeypatch.setattr(KernelIndex, "_valid", counting)
        index.replace_pods(pods)
        for pod in pods:
            index.apply("ADDED", pod)
        assert all(index.get(k) is not None for k in kernel_ids)
        assert checks <= 4 * count
