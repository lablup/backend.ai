"""Turn listed API objects into the inputs of one scheduling cycle."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any, Final

from kubernetes.utils.quantity import parse_quantity

from ai.backend.kube.controller.naming import (
    ANNOTATION_DEVICES,
    ANNOTATION_POD_GROUP,
    ANNOTATION_SHARED_DEVICES,
    HOSTNAME_LABEL,
    LABEL_MANAGED_BY,
    LABEL_QUEUE,
    MANAGED_BY,
    SOKOVAN_GATE,
    SOKOVAN_SCHEDULER,
)
from ai.backend.kube.crd.scheduling import BindRequestPhase, PodGroupPhase
from ai.backend.kube.scheduler.cycle import (
    NodeState,
    PendingGroup,
    PendingPod,
    QueueState,
    Resources,
    Taint,
    Toleration,
    queue_chain,
)

_UNLIMITED: Final = 2**62
_ENDED_POD_PHASES: Final = frozenset({"Succeeded", "Failed"})

type PodKey = tuple[str, str]  # namespace, name


def _milli(value: Any) -> int:
    return math.ceil(Decimal(str(parse_quantity(value))) * 1000)


def _bytes(value: Any) -> int:
    return math.ceil(Decimal(str(parse_quantity(value))))


def pod_requests(pod: Mapping[str, Any]) -> Resources:
    """Effective requests: the larger of the app containers' sum and any init container."""
    spec = pod.get("spec", {})

    def total(containers: Iterable[Mapping[str, Any]]) -> tuple[int, int]:
        cpu = mem = 0
        for c in containers:
            req = (c.get("resources") or {}).get("requests") or {}
            cpu += _milli(req["cpu"]) if "cpu" in req else 0
            mem += _bytes(req["memory"]) if "memory" in req else 0
        return cpu, mem

    cpu, mem = total(spec.get("containers", []))
    for init in spec.get("initContainers") or []:
        icpu, imem = total([init])
        cpu, mem = max(cpu, icpu), max(mem, imem)
    return Resources(cpu, mem, 1)


def pod_devices(pod: Mapping[str, Any], annotation: str = ANNOTATION_DEVICES) -> dict[str, int]:
    """DRA driver → devices the Pod's claims ask for, as the session controller recorded them."""
    raw = (pod["metadata"].get("annotations") or {}).get(annotation)
    if not raw:
        return {}
    return {str(driver): int(count) for driver, count in json.loads(raw).items()}


def is_gated(pod: Mapping[str, Any]) -> bool:
    gates = pod.get("spec", {}).get("schedulingGates") or []
    return any(g.get("name") == SOKOVAN_GATE for g in gates)


def in_flight_binds(bind_requests: Iterable[Mapping[str, Any]]) -> dict[PodKey, str]:
    """Pods with a BindRequest the binder has not failed → the node chosen for them."""
    binds = {}
    for br in bind_requests:
        if (br.get("status") or {}).get("phase") == BindRequestPhase.FAILED:
            continue
        spec = br["spec"]
        binds[br["metadata"]["namespace"], spec["podName"]] = str(spec["selectedNode"])
    return binds


def _key(pod: Mapping[str, Any]) -> PodKey:
    return pod["metadata"].get("namespace", ""), pod["metadata"]["name"]


def _awaits_sokovan(pod: Mapping[str, Any]) -> bool:
    spec = pod.get("spec", {})
    return not spec.get("nodeName") and (
        is_gated(pod) or spec.get("schedulerName") == SOKOVAN_SCHEDULER
    )


def _target_node(pod: Mapping[str, Any], in_flight: Mapping[PodKey, str]) -> str | None:
    """The node a pod holds resources on: bound, chosen in a BindRequest, or released by
    sokovan and pinned."""
    spec = pod.get("spec", {})
    if spec.get("nodeName"):
        return str(spec["nodeName"])
    if (node := in_flight.get(_key(pod))) is not None:
        return node
    if _awaits_sokovan(pod):
        return None
    return (spec.get("nodeSelector") or {}).get(HOSTNAME_LABEL)


def _holds_resources(pod: Mapping[str, Any]) -> bool:
    return pod.get("status", {}).get("phase") not in _ENDED_POD_PHASES


def build_nodes(
    nodes: Iterable[Mapping[str, Any]],
    pods: Iterable[Mapping[str, Any]],
    resource_slices: Iterable[Mapping[str, Any]] = (),
    resource_claims: Iterable[Mapping[str, Any]] = (),
    in_flight: Mapping[PodKey, str] | None = None,
) -> list[NodeState]:
    used: dict[str, Resources] = defaultdict(Resources)
    devices_used: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for pod in pods:
        target = _target_node(pod, in_flight or {})
        if target is not None and _holds_resources(pod):
            used[target] = used[target] + pod_requests(pod)
            for driver, count in pod_devices(pod).items():
                devices_used[target][driver] += count
    devices: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    slot_of: dict[tuple[str, str, str], str] = {}  # (driver, pool, device) → slot
    for rs in resource_slices:
        spec = rs.get("spec", {})
        if not spec.get("nodeName"):
            continue
        node, driver = spec["nodeName"], spec["driver"]
        for device in spec.get("devices") or []:
            slot = _slot_name(driver, device)
            devices[node][driver] += 1
            devices[node][f"{driver}/{slot}"] += 1
            slot_of[driver, spec["pool"]["name"], device["name"]] = slot
    for claim in resource_claims:
        # Claims of Backend.AI sessions are counted from their Pods, even before allocation.
        if (claim["metadata"].get("labels") or {}).get(LABEL_MANAGED_BY) == MANAGED_BY:
            continue
        for result in _allocated(claim):
            if result.get("shareID"):
                continue  # a share leaves the device to others; the allocator weighs it
            used_slot = slot_of.get((result["driver"], result["pool"], result["device"]))
            if used_slot is not None:
                devices_used[result["pool"]][f"{result['driver']}/{used_slot}"] += 1
    states = []
    for node in nodes:
        meta, spec, status = node["metadata"], node.get("spec", {}), node.get("status", {})
        alloc = status.get("allocatable", {})
        ready = any(
            c.get("type") == "Ready" and c.get("status") == "True"
            for c in status.get("conditions") or []
        )
        states.append(
            NodeState(
                name=meta["name"],
                allocatable=Resources(
                    _milli(alloc.get("cpu", "0")),
                    _bytes(alloc.get("memory", "0")),
                    int(alloc.get("pods", "110")),
                ),
                used=used[meta["name"]],
                labels=meta.get("labels") or {},
                taints=[
                    Taint(t["key"], t.get("value"), t["effect"]) for t in spec.get("taints") or []
                ],
                schedulable=ready and not spec.get("unschedulable", False),
                devices=dict(devices[meta["name"]]),
                devices_used=dict(devices_used[meta["name"]]),
            )
        )
    return states


def _slot_name(driver: str, device: Mapping[str, Any]) -> str:
    """bai-dra devices carry the Backend.AI slot they serve; others go by driver."""
    attribute = (device.get("attributes") or {}).get("slotName") or {}
    return str(attribute.get("string") or driver)


def _allocated(claim: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    allocation = (claim.get("status") or {}).get("allocation") or {}
    results: list[Mapping[str, Any]] = (allocation.get("devices") or {}).get("results") or []
    return results


def _slot_limit(resources: Mapping[str, Any]) -> Resources | None:
    if not resources:
        return None
    cpu = resources.get("cpu", {}).get("limit")
    mem = resources.get("mem", {}).get("limit")
    if cpu is None and mem is None:
        return None
    return Resources(
        math.ceil(Decimal(cpu) * 1000) if cpu is not None else _UNLIMITED,
        math.ceil(Decimal(mem)) if mem is not None else _UNLIMITED,
        _UNLIMITED,
    )


def build_queues(
    queues: Iterable[Mapping[str, Any]],
    pods: Iterable[Mapping[str, Any]],
    in_flight: Mapping[PodKey, str] | None = None,
) -> dict[str, QueueState]:
    states = {
        q["metadata"]["name"]: QueueState(
            name=q["metadata"]["name"],
            limit=_slot_limit(q.get("spec", {}).get("resources") or {}),
            parent=q.get("spec", {}).get("parentQueue"),
            fair_share_factor=float((q.get("status") or {}).get("fairShareFactor") or 0.0),
        )
        for q in queues
    }
    for pod in pods:
        queue = (pod["metadata"].get("labels") or {}).get(LABEL_QUEUE)
        if queue is None or _target_node(pod, in_flight or {}) is None:
            continue
        if not _holds_resources(pod):
            continue
        for state in queue_chain(states, queue):
            state.used = state.used + pod_requests(pod)
    return states


def build_pending_groups(
    pod_groups: Iterable[Mapping[str, Any]],
    pods: Iterable[Mapping[str, Any]],
    in_flight: Mapping[PodKey, str] | None = None,
) -> list[PendingGroup]:
    gated: dict[tuple[str, str], list[PendingPod]] = defaultdict(list)
    for pod in pods:
        meta = pod["metadata"]
        group = (meta.get("annotations") or {}).get(ANNOTATION_POD_GROUP)
        if group is None or not _awaits_sokovan(pod) or meta.get("deletionTimestamp"):
            continue
        if _key(pod) in (in_flight or {}):
            continue
        spec = pod.get("spec", {})
        gated[meta["namespace"], group].append(
            PendingPod(
                namespace=meta["namespace"],
                name=meta["name"],
                requests=pod_requests(pod),
                node_selector=spec.get("nodeSelector") or {},
                tolerations=[
                    Toleration(
                        t.get("key"), t.get("operator", "Equal"), t.get("value"), t.get("effect")
                    )
                    for t in spec.get("tolerations") or []
                ],
                devices=pod_devices(pod),
                shared_devices=pod_devices(pod, ANNOTATION_SHARED_DEVICES),
            )
        )
    groups = []
    for pg in pod_groups:
        meta, spec = pg["metadata"], pg["spec"]
        phase = (pg.get("status") or {}).get("phase", PodGroupPhase.PENDING)
        key = (meta["namespace"], meta["name"])
        # A Scheduled group whose Pods wait again lost its BindRequests (binder failure,
        # timeout): it is placed anew.
        placeable = (PodGroupPhase.PENDING, PodGroupPhase.ADMITTED, PodGroupPhase.SCHEDULED)
        if phase not in placeable or key not in gated:
            continue
        groups.append(
            PendingGroup(
                namespace=meta["namespace"],
                name=meta["name"],
                queue=spec["queue"],
                priority=spec.get("priority", 0),
                created_at=meta.get("creationTimestamp", ""),
                min_member=spec["minMember"],
                pods=gated[key],
                required_levels=(spec.get("topology") or {}).get("requiredLevels") or [],
            )
        )
    return groups
