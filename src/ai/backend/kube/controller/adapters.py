"""Scheduler adapters: what a session's Pods carry for the scheduler of the cluster
(suggestion-1122 3.6). `SessionWorkload.spec.schedulerName` names the adapter.

| adapter | gang | queue | devices |
|---|---|---|---|
| sokovan | PodGroup | Queue | sokovan + DRA allocator |
| kueue | pod group labels | LocalQueue → ClusterQueue | kube-scheduler |
| kube | none: single-node sessions only | none | kube-scheduler |
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, Final, override

from ai.backend.kube.controller.naming import (
    ANNOTATION_POD_GROUP,
    HOSTNAME_LABEL,
    LABEL_SESSION_ID,
    SOKOVAN_DEDICATED_TAINT,
    SOKOVAN_GATE,
    SOKOVAN_SCHEDULER,
    session_queue,
)
from ai.backend.kube.crd.scheduling import SokovanBindMode
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.kube.errors import InvalidSessionWorkloadError

KUEUE_SCHEDULER: Final = "kueue"
KUBE_SCHEDULER: Final = "kube"
KUEUE_QUEUE_LABEL: Final = "kueue.x-k8s.io/queue-name"
KUEUE_POD_GROUP_LABEL: Final = "kueue.x-k8s.io/pod-group-name"
KUEUE_POD_GROUP_COUNT: Final = "kueue.x-k8s.io/pod-group-total-count"
KUEUE_GATE: Final = "kueue.x-k8s.io/admission"


@dataclass(frozen=True)
class Capabilities:
    gang: bool
    devices_by_sokovan: bool


@dataclass(frozen=True)
class PodScheduling:
    spec: Mapping[str, Any]  # schedulerName, schedulingGates, affinity
    labels: Mapping[str, str]
    annotations: Mapping[str, str]


class SchedulerAdapter(ABC):
    name: ClassVar[str]
    capabilities: ClassVar[Capabilities]

    def validate(self, workload: SessionWorkload) -> None:
        """Reject what the scheduler cannot run."""
        if not self.capabilities.gang and _spans_nodes(workload):
            raise InvalidSessionWorkloadError(
                f"scheduler {self.name} has no gang scheduling; multi-node sessions need sokovan"
                " or kueue"
            )

    @abstractmethod
    def pod(self, workload: SessionWorkload) -> PodScheduling:
        raise NotImplementedError

    def group_objects(self, workload: SessionWorkload) -> list[dict[str, Any]]:
        """Objects created beside the Pods (a gang, a queue)."""
        return []


class SokovanAdapter(SchedulerAdapter):
    name = SOKOVAN_SCHEDULER
    capabilities = Capabilities(gang=True, devices_by_sokovan=True)
    _bind_mode: SokovanBindMode

    def __init__(self, bind_mode: SokovanBindMode) -> None:
        self._bind_mode = bind_mode

    @override
    def pod(self, workload: SessionWorkload) -> PodScheduling:
        """sokovan holds each Pod at a scheduling gate until the whole group fits. With the binder
        the Pod names sokovan as its scheduler, so kube-scheduler never takes it."""
        binder = self._bind_mode == SokovanBindMode.BINDER
        spec: dict[str, Any] = {
            "schedulerName": SOKOVAN_SCHEDULER if binder else "default-scheduler",
            "schedulingGates": [{"name": SOKOVAN_GATE}],
        }
        if binder:
            # sokovan owns the nodes carrying the taint; only kernel Pods tolerate it.
            spec["tolerations"] = [
                {
                    "key": SOKOVAN_DEDICATED_TAINT,
                    "operator": "Equal",
                    "value": "true",
                    "effect": "NoSchedule",
                }
            ]
        return PodScheduling(
            spec=spec,
            labels={},
            annotations={ANNOTATION_POD_GROUP: workload.metadata["name"]},
        )


class KueueAdapter(SchedulerAdapter):
    """Kueue's pod integration admits the group; kube-scheduler places and allocates devices."""

    name = KUEUE_SCHEDULER
    capabilities = Capabilities(gang=True, devices_by_sokovan=False)
    _cluster_queue: str

    def __init__(self, cluster_queue: str) -> None:
        self._cluster_queue = cluster_queue

    @override
    def pod(self, workload: SessionWorkload) -> PodScheduling:
        labels = {KUEUE_QUEUE_LABEL: session_queue(workload)}
        annotations: dict[str, str] = {}
        if len(workload.spec.kernels) > 1:
            labels[KUEUE_POD_GROUP_LABEL] = workload.metadata["name"]
            annotations[KUEUE_POD_GROUP_COUNT] = str(len(workload.spec.kernels))
        return PodScheduling(
            spec={"schedulerName": "default-scheduler", **_single_node_affinity(workload)},
            labels=labels,
            annotations=annotations,
        )

    @override
    def group_objects(self, workload: SessionWorkload) -> list[dict[str, Any]]:
        return [
            {
                "apiVersion": "kueue.x-k8s.io/v1beta2",
                "kind": "LocalQueue",
                "metadata": {
                    "name": session_queue(workload),
                    "namespace": workload.metadata["namespace"],
                },
                "spec": {"clusterQueue": self._cluster_queue},
            }
        ]


class KubeAdapter(SchedulerAdapter):
    """The default kube-scheduler, without a gang: single-node sessions only."""

    name = KUBE_SCHEDULER
    capabilities = Capabilities(gang=False, devices_by_sokovan=False)

    @override
    def pod(self, workload: SessionWorkload) -> PodScheduling:
        return PodScheduling(
            spec={"schedulerName": "default-scheduler", **_single_node_affinity(workload)},
            labels={},
            annotations={},
        )


def _spans_nodes(workload: SessionWorkload) -> bool:
    return workload.spec.cluster_mode == "multi-node" and len(workload.spec.kernels) > 1


def _single_node_affinity(workload: SessionWorkload) -> dict[str, Any]:
    """Kernels of a single-node session share a node. The first Pod matches its own selector."""
    if workload.spec.cluster_mode != "single-node" or len(workload.spec.kernels) < 2:
        return {}
    return {
        "affinity": {
            "podAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": [
                    {
                        "labelSelector": {
                            "matchLabels": {LABEL_SESSION_ID: workload.spec.session_id}
                        },
                        "topologyKey": HOSTNAME_LABEL,
                    }
                ]
            }
        }
    }


def pod_pending_reason(pods: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    """Why kube-scheduler or Kueue has not placed the Pods yet."""
    for pod in pods:
        gates = {g.get("name") for g in pod.get("spec", {}).get("schedulingGates") or []}
        if KUEUE_GATE in gates:
            return "QueueAdmission", "waiting for Kueue to admit the session"
        for cond in (pod.get("status") or {}).get("conditions") or []:
            if cond.get("type") == "PodScheduled" and cond.get("status") == "False":
                return cond.get("reason"), cond.get("message")
    return None, None


def build_adapters(
    bind_mode: SokovanBindMode, kueue_cluster_queue: str
) -> dict[str, SchedulerAdapter]:
    return {
        SOKOVAN_SCHEDULER: SokovanAdapter(bind_mode),
        KUEUE_SCHEDULER: KueueAdapter(kueue_cluster_queue),
        KUBE_SCHEDULER: KubeAdapter(),
    }


def adapter_for(
    adapters: Mapping[str, SchedulerAdapter], workload: SessionWorkload
) -> SchedulerAdapter:
    adapter = adapters.get(workload.spec.scheduler_name)
    if adapter is None:
        raise InvalidSessionWorkloadError(
            f"unknown scheduler {workload.spec.scheduler_name!r}; known: {', '.join(adapters)}"
        )
    return adapter
