from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.backend.kube.controller.naming import (
    KERNEL_CONTAINER,
    LABEL_KERNEL_ID,
    LABEL_SESSION_ID,
)


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
    uid: int | None
    gid: int | None


def endpoint_from_pod(pod: dict[str, Any]) -> KernelEndpoint | None:
    meta = pod["metadata"]
    labels = meta.get("labels") or {}
    kernel_id = labels.get(LABEL_KERNEL_ID)
    if kernel_id is None:
        return None
    env: dict[str, str] = {}
    for container in pod.get("spec", {}).get("containers", []):
        if container["name"] == KERNEL_CONTAINER:
            env = {e["name"]: e.get("value", "") for e in container.get("env", [])}
    owner = next(
        (r["name"] for r in meta.get("ownerReferences") or [] if r["kind"] == "SessionWorkload"),
        None,
    )
    return KernelEndpoint(
        kernel_id=kernel_id,
        session_id=labels[LABEL_SESSION_ID],
        namespace=meta["namespace"],
        pod_name=meta["name"],
        pod_uid=meta["uid"],
        pod_ip=pod.get("status", {}).get("podIP"),
        pod_phase=pod.get("status", {}).get("phase"),
        workload_name=owner,
        uid=int(env["LOCAL_USER_ID"]) if "LOCAL_USER_ID" in env else None,
        gid=int(env["LOCAL_GROUP_ID"]) if "LOCAL_GROUP_ID" in env else None,
    )


class KernelIndex:
    """Kernel id → its Pod, kept up to date from a Pod watch."""

    _by_kernel: dict[str, KernelEndpoint]

    def __init__(self) -> None:
        self._by_kernel = {}

    def apply(self, event: str, pod: dict[str, Any]) -> None:
        endpoint = endpoint_from_pod(pod)
        if endpoint is None:
            return
        if event == "DELETED":
            current = self._by_kernel.get(endpoint.kernel_id)
            if current is not None and current.pod_uid == endpoint.pod_uid:
                del self._by_kernel[endpoint.kernel_id]
            return
        self._by_kernel[endpoint.kernel_id] = endpoint

    def get(self, kernel_id: str) -> KernelEndpoint | None:
        return self._by_kernel.get(kernel_id)
