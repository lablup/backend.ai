from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Final

from ai.backend.kube.controller.naming import (
    KERNEL_CONTAINER,
    LABEL_KERNEL_ID,
    LABEL_SESSION_ID,
)
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

# Written by the session controller on every kernel Pod (decimal strings).
ANNOTATION_KERNEL_UID: Final = "backend.ai/kernel-uid"
ANNOTATION_KERNEL_GID: Final = "backend.ai/kernel-gid"
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
    node_name: str | None
    uid: int | None
    gid: int | None


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


def _workload_owner(meta: Mapping[str, Any]) -> str | None:
    crd = SessionWorkload.crd
    for ref in meta.get("ownerReferences") or []:
        if ref.get("kind") == crd.kind and str(ref.get("apiVersion", "")).startswith(
            f"{crd.group}/"
        ):
            return str(ref["name"])
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
        workload_name=owner,
        node_name=(pod.get("spec") or {}).get("nodeName"),
        uid=uid,
        gid=gid,
    )


class KernelIndex:
    """Kernel id → its Pod, kept up to date from a Pod watch and a namespace watch.

    Only Pods in namespaces the Manager labeled are indexed; a kernel id stays with the first
    Pod that claimed it while that Pod exists.
    """

    _candidates: dict[str, KernelEndpoint]  # pod uid → endpoint, in any namespace
    _by_kernel: dict[str, str]  # kernel id → pod uid
    _namespaces: set[str]
    _ignored: set[str]  # pod uids logged as duplicates
    _on_removed: Callable[[str], None] | None

    def __init__(self, on_removed: Callable[[str], None] | None = None) -> None:
        self._candidates = {}
        self._by_kernel = {}
        self._namespaces = set()
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
        if event == "DELETED":
            self._candidates.pop(uid, None)
        else:
            endpoint = endpoint_from_pod(pod)
            if endpoint is None:
                self._candidates.pop(uid, None)
            else:
                self._candidates[uid] = endpoint
        self._resolve()

    def replace_pods(self, pods: list[dict[str, Any]]) -> None:
        """Relist handler: the Pods that exist now."""
        try:
            fresh: dict[str, KernelEndpoint] = {}
            for pod in pods:
                if (endpoint := endpoint_from_pod(pod)) is not None:
                    fresh[endpoint.pod_uid] = endpoint
            self._candidates = fresh
            self._resolve()
        except Exception:
            log.exception("kernel pod relist skipped")

    def apply_namespace(self, event: str, namespace: dict[str, Any]) -> None:
        """Namespace watch handler; never raises."""
        try:
            meta = namespace["metadata"]
            labels = meta.get("labels") or {}
            managed = labels.get(LABEL_NAMESPACE_MANAGED_BY) == NAMESPACE_MANAGED_BY
            if event != "DELETED" and managed:
                self._namespaces.add(str(meta["name"]))
            else:
                self._namespaces.discard(str(meta["name"]))
            self._resolve()
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
            self._resolve()
        except Exception:
            log.exception("namespace relist skipped")

    def _resolve(self) -> None:
        """Keep each kernel id with its first live Pod in a managed namespace."""
        resolved: dict[str, str] = {}
        for kernel_id, pod_uid in self._by_kernel.items():
            endpoint = self._candidates.get(pod_uid)
            if endpoint is not None and endpoint.namespace in self._namespaces:
                resolved[kernel_id] = pod_uid
        for pod_uid, endpoint in self._candidates.items():
            if endpoint.namespace not in self._namespaces:
                continue
            current = resolved.get(endpoint.kernel_id)
            if current is None:
                resolved[endpoint.kernel_id] = pod_uid
            elif current != pod_uid and pod_uid not in self._ignored:
                self._ignored.add(pod_uid)
                log.warning(
                    "duplicate kernel pod ignored",
                    kernel_id=endpoint.kernel_id,
                    k8s_namespace=endpoint.namespace,
                    pod_name=endpoint.pod_name,
                )
        removed = [
            kernel_id
            for kernel_id, pod_uid in self._by_kernel.items()
            if resolved.get(kernel_id) != pod_uid
        ]
        self._by_kernel = resolved
        self._ignored &= self._candidates.keys()
        if self._on_removed is not None:
            for kernel_id in removed:
                self._on_removed(kernel_id)

    def get(self, kernel_id: str) -> KernelEndpoint | None:
        pod_uid = self._by_kernel.get(kernel_id)
        return self._candidates.get(pod_uid) if pod_uid is not None else None

    def kernel_ids(self) -> Iterable[str]:
        return list(self._by_kernel)
