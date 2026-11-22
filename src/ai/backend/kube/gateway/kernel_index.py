from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Final

from ai.backend.kube.controller.naming import (
    ANNOTATION_KERNEL_GID,
    ANNOTATION_KERNEL_UID,
    KERNEL_CONTAINER,
    LABEL_KERNEL_ID,
    LABEL_SESSION_ID,
)
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

# Session namespaces carry this label, set by the Manager when it creates them.
LABEL_NAMESPACE_MANAGED_BY: Final = "app.kubernetes.io/managed-by"
NAMESPACE_MANAGED_BY: Final = "backendai-manager"
_MAX_ID: Final = 2**32 - 1


@dataclass(frozen=True)
class KernelEndpoint:
    kernel_id: str
    session_id: str
    namespace: str
    pod_name: str
    pod_uid: str
    pod_ip: str | None
    pod_phase: str | None
    workload_name: str | None
    workload_uid: str | None
    node_name: str | None
    uid: int | None
    gid: int | None


@dataclass(frozen=True)
class WorkloadKernels:
    """What the index reads of a SessionWorkload: where it is and the kernels it declares."""

    namespace: str
    session_id: str
    kernel_ids: frozenset[str]


def parse_id(value: object) -> int | None:
    """A uid or gid given as a decimal string; anything else is unknown."""
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        return None
    parsed = int(value)
    return parsed if parsed <= _MAX_ID else None


def _kernel_ids(pod: Mapping[str, Any]) -> tuple[int | None, int | None]:
    annotations = pod["metadata"].get("annotations") or {}
    uid = parse_id(annotations.get(ANNOTATION_KERNEL_UID))
    gid = parse_id(annotations.get(ANNOTATION_KERNEL_GID))
    if uid is not None:
        return uid, gid
    # Pods created before the annotations: the environ the controller rendered.
    env: dict[str, object] = {}
    for container in pod.get("spec", {}).get("containers") or []:
        if container.get("name") == KERNEL_CONTAINER:
            env = {e.get("name"): e.get("value") for e in container.get("env") or []}
    return parse_id(env.get("LOCAL_USER_ID")), parse_id(env.get("LOCAL_GROUP_ID"))


def _workload_owner(meta: Mapping[str, Any]) -> tuple[str, str] | None:
    """The name and uid of the SessionWorkload owning an object."""
    crd = SessionWorkload.crd
    for ref in meta.get("ownerReferences") or []:
        if (
            ref.get("kind") == crd.kind
            and str(ref.get("apiVersion", "")).startswith(f"{crd.group}/")
            and ref.get("uid")
        ):
            return str(ref["name"]), str(ref["uid"])
    return None


def endpoint_from_pod(pod: Mapping[str, Any]) -> KernelEndpoint | None:
    """The kernel a Pod runs; None unless it is a kernel Pod owned by a SessionWorkload."""
    meta = pod["metadata"]
    labels = meta.get("labels") or {}
    kernel_id = labels.get(LABEL_KERNEL_ID)
    session_id = labels.get(LABEL_SESSION_ID)
    owner = _workload_owner(meta)
    if kernel_id is None or session_id is None or owner is None:
        return None
    uid, gid = _kernel_ids(pod)
    status = pod.get("status") or {}
    return KernelEndpoint(
        kernel_id=str(kernel_id),
        session_id=str(session_id),
        namespace=str(meta["namespace"]),
        pod_name=str(meta["name"]),
        pod_uid=str(meta["uid"]),
        pod_ip=status.get("podIP"),
        pod_phase=status.get("phase"),
        workload_name=owner[0],
        workload_uid=owner[1],
        node_name=(pod.get("spec") or {}).get("nodeName"),
        uid=uid,
        gid=gid,
    )


def workload_kernels(workload: Mapping[str, Any]) -> tuple[str, WorkloadKernels]:
    """The uid of a SessionWorkload and the kernels it declares."""
    meta, spec = workload["metadata"], workload.get("spec") or {}
    return str(meta["uid"]), WorkloadKernels(
        namespace=str(meta["namespace"]),
        session_id=str(spec.get("sessionId", "")),
        kernel_ids=frozenset(
            str(k["kernelId"]) for k in spec.get("kernels") or [] if k.get("kernelId")
        ),
    )


class KernelIndex:
    """Kernel id → its Pod, kept up to date from watches of Pods, namespaces and
    SessionWorkloads.

    A Pod counts only in a namespace the Manager labeled, owned (by uid) by a SessionWorkload
    of that namespace that declares its session id and kernel id. A kernel id stays with the
    first Pod that claimed it while that Pod exists. An event resolves only the kernel ids it
    touches; a relist resolves each kernel id once.
    """

    _candidates: dict[str, KernelEndpoint]  # pod uid → endpoint, in any namespace
    _pods_of_kernel: dict[str, dict[str, None]]  # kernel id → pod uids, first seen first
    _kernels_of_namespace: dict[str, set[str]]  # namespace → kernel ids of its candidates
    _kernels_of_workload: dict[str, set[str]]  # workload uid → kernel ids of its candidates
    _by_kernel: dict[str, str]  # kernel id → pod uid
    _namespaces: set[str]
    _workloads: dict[str, WorkloadKernels]  # workload uid → its kernels
    _ignored: set[str]  # pod uids logged as duplicates
    _on_removed: Callable[[str], None] | None

    def __init__(self, on_removed: Callable[[str], None] | None = None) -> None:
        self._candidates = {}
        self._pods_of_kernel = {}
        self._kernels_of_namespace = {}
        self._kernels_of_workload = {}
        self._by_kernel = {}
        self._namespaces = set()
        self._workloads = {}
        self._ignored = set()
        self._on_removed = on_removed

    def apply(self, event: str, pod: dict[str, Any]) -> None:
        """Pod watch handler; never raises."""
        try:
            self._apply(event, pod)
        except Exception:
            log.exception("kernel pod event skipped")

    def _apply(self, event: str, pod: Mapping[str, Any]) -> None:
        uid = str(pod["metadata"]["uid"])
        endpoint = None if event == "DELETED" else endpoint_from_pod(pod)
        touched: set[str] = set()
        if (previous := self._drop_candidate(uid)) is not None:
            touched.add(previous.kernel_id)
        if endpoint is not None:
            self._add_candidate(endpoint)
            touched.add(endpoint.kernel_id)
        self._resolve(touched)

    def _add_candidate(self, endpoint: KernelEndpoint) -> None:
        self._candidates[endpoint.pod_uid] = endpoint
        self._pods_of_kernel.setdefault(endpoint.kernel_id, {})[endpoint.pod_uid] = None
        self._kernels_of_namespace.setdefault(endpoint.namespace, set()).add(endpoint.kernel_id)
        if endpoint.workload_uid is not None:
            self._kernels_of_workload.setdefault(endpoint.workload_uid, set()).add(
                endpoint.kernel_id
            )

    def _drop_candidate(self, pod_uid: str) -> KernelEndpoint | None:
        """Forget a Pod. Its kernel id stays in the namespace and workload sets until the next
        relist; resolving it again is harmless."""
        endpoint = self._candidates.pop(pod_uid, None)
        if endpoint is None:
            return None
        pods = self._pods_of_kernel.get(endpoint.kernel_id)
        if pods is not None:
            pods.pop(pod_uid, None)
            if not pods:
                del self._pods_of_kernel[endpoint.kernel_id]
        self._ignored.discard(pod_uid)
        return endpoint

    def replace_pods(self, pods: list[dict[str, Any]]) -> None:
        """Relist handler: the Pods that exist now."""
        try:
            self._candidates = {}
            self._pods_of_kernel = {}
            self._kernels_of_namespace = {}
            self._kernels_of_workload = {}
            for pod in pods:
                if (endpoint := endpoint_from_pod(pod)) is not None:
                    self._add_candidate(endpoint)
            self._ignored &= self._candidates.keys()
            self._resolve_all()
        except Exception:
            log.exception("kernel pod relist skipped")

    def apply_namespace(self, event: str, namespace: dict[str, Any]) -> None:
        """Namespace watch handler; never raises."""
        try:
            meta = namespace["metadata"]
            name = str(meta["name"])
            labels = meta.get("labels") or {}
            managed = labels.get(LABEL_NAMESPACE_MANAGED_BY) == NAMESPACE_MANAGED_BY
            if event != "DELETED" and managed:
                self._namespaces.add(name)
            else:
                self._namespaces.discard(name)
            self._resolve(set(self._kernels_of_namespace.get(name, ())))
        except Exception:
            log.exception("namespace event skipped")

    def replace_namespaces(self, namespaces: list[dict[str, Any]]) -> None:
        try:
            self._namespaces = {
                str(ns["metadata"]["name"])
                for ns in namespaces
                if (ns["metadata"].get("labels") or {}).get(LABEL_NAMESPACE_MANAGED_BY)
                == NAMESPACE_MANAGED_BY
            }
            self._resolve_all()
        except Exception:
            log.exception("namespace relist skipped")

    def apply_workload(self, event: str, workload: dict[str, Any]) -> None:
        """SessionWorkload watch handler; never raises."""
        try:
            uid, kernels = workload_kernels(workload)
            if event == "DELETED":
                self._workloads.pop(uid, None)
            else:
                self._workloads[uid] = kernels
            self._resolve(set(self._kernels_of_workload.get(uid, ())))
        except Exception:
            log.exception("session workload event skipped")

    def replace_workloads(self, workloads: list[dict[str, Any]]) -> None:
        """Relist handler: the SessionWorkloads that exist now."""
        try:
            self._workloads = dict(workload_kernels(w) for w in workloads)
            self._resolve_all()
        except Exception:
            log.exception("session workload relist skipped")

    def _valid(self, endpoint: KernelEndpoint) -> bool:
        if endpoint.namespace not in self._namespaces or endpoint.workload_uid is None:
            return False
        workload = self._workloads.get(endpoint.workload_uid)
        return (
            workload is not None
            and workload.namespace == endpoint.namespace
            and workload.session_id == endpoint.session_id
            and endpoint.kernel_id in workload.kernel_ids
        )

    def _resolve_all(self) -> None:
        self._resolve(self._by_kernel.keys() | self._pods_of_kernel.keys())

    def _resolve(self, kernel_ids: Iterable[str]) -> None:
        """Keep each of `kernel_ids` with its current Pod while valid, else its first valid
        Pod."""
        removed = []
        for kernel_id in kernel_ids:
            current = self._by_kernel.get(kernel_id)
            endpoint = self._candidates.get(current) if current is not None else None
            chosen: str | None = current
            if endpoint is None or not self._valid(endpoint):
                chosen = next(
                    (
                        pod_uid
                        for pod_uid in self._pods_of_kernel.get(kernel_id, ())
                        if self._valid(self._candidates[pod_uid])
                    ),
                    None,
                )
            if chosen is None:
                self._by_kernel.pop(kernel_id, None)
            else:
                self._by_kernel[kernel_id] = chosen
                self._warn_duplicates(kernel_id, chosen)
            if current is not None and chosen != current:
                removed.append(kernel_id)
        if self._on_removed is not None:
            for kernel_id in removed:
                self._on_removed(kernel_id)

    def _warn_duplicates(self, kernel_id: str, chosen: str) -> None:
        for pod_uid in self._pods_of_kernel.get(kernel_id, ()):
            if pod_uid == chosen or pod_uid in self._ignored:
                continue
            endpoint = self._candidates[pod_uid]
            if self._valid(endpoint):
                self._ignored.add(pod_uid)
                log.warning(
                    "duplicate kernel pod ignored",
                    kernel_id=kernel_id,
                    k8s_namespace=endpoint.namespace,
                    pod_name=endpoint.pod_name,
                )

    def get(self, kernel_id: str) -> KernelEndpoint | None:
        pod_uid = self._by_kernel.get(kernel_id)
        return self._candidates.get(pod_uid) if pod_uid is not None else None

    def kernel_ids(self) -> Iterable[str]:
        return list(self._by_kernel)
