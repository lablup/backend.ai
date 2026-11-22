"""Turn listed API objects into the inputs of one scheduling cycle."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Final

from kubernetes.utils.quantity import parse_quantity
from pydantic import ValidationError

from ai.backend.kube.controller.naming import (
    ANNOTATION_DEVICES,
    ANNOTATION_SHARED_DEVICES,
    HOSTNAME_LABEL,
    LABEL_MANAGED_BY,
    LABEL_SESSION_GROUP,
    LABEL_SESSION_ID,
    MANAGED_BY,
    SOKOVAN_GATE,
    SOKOVAN_SCHEDULER,
)
from ai.backend.kube.crd.scheduling import BindRequestPhase
from ai.backend.kube.crd.session import PlacementPhase, SessionGroupSpec, SessionPhase
from ai.backend.kube.scheduler.cycle import (
    GroupPolicy,
    NodeState,
    PendingGroup,
    PendingPod,
    Resources,
    ShareClaim,
    ShareOption,
    ShareRequest,
    Taint,
    Toleration,
)

_ENDED_POD_PHASES: Final = frozenset({"Succeeded", "Failed"})
_NATIVE_RESOURCES: Final = frozenset({"cpu", "memory", "ephemeral-storage", "pods"})
# The capacity of a device in 0.01-share units: the bare key of bai-dra, or qualified.
SHARES_CAPACITIES: Final = ("shares", "dra.backend.ai/shares")
_FRACTION: Final = "fraction"
# In binder mode, sokovan owns only the nodes carrying this taint (NoSchedule).
DEDICATED_TAINT_KEY: Final = "sokovan.backend.ai/dedicated"
DEDICATED_TAINT_VALUE: Final = "true"
# NVKE marks a node that is to be recycled; nothing new goes there.
NEEDS_RECYCLE_CONDITION: Final = "nvke.nvidia.com/NeedsRecycle"

type PodKey = tuple[str, str]  # namespace, name
type PodUid = str
type ClaimKey = tuple[str, str]  # namespace, name
type SessionKey = tuple[str, str]  # namespace, SessionWorkload name
type SessionIndex = Mapping[tuple[str, str], str]  # (namespace, session id) → SessionWorkload
_UNPLACEABLE_PHASES: Final = frozenset({
    SessionPhase.TERMINATING,
    SessionPhase.TERMINATED,
    SessionPhase.ERROR,
})


@dataclass(frozen=True)
class SlotProfile:
    """What sokovan reads of a DeviceProfile."""

    slot_name: str
    driver: str
    device_class: str
    sharing_mode: str
    extended_resource: str | None


def slot_profiles(profiles: Iterable[Mapping[str, Any]]) -> list[SlotProfile]:
    out = []
    for p in profiles:
        spec = p.get("spec") or {}
        try:
            out.append(
                SlotProfile(
                    slot_name=str(spec["slotName"]),
                    driver=str(spec["driverName"]),
                    device_class=str(spec["deviceClassName"]),
                    sharing_mode=str(spec.get("sharingMode", "")),
                    extended_resource=spec.get("extendedResourceName"),
                )
            )
        except KeyError:
            continue
    return out


def _milli(value: Any) -> int:
    return math.ceil(Decimal(str(parse_quantity(value))) * 1000)


def _bytes(value: Any) -> int:
    return math.ceil(Decimal(str(parse_quantity(value))))


def _is_extended(name: str) -> bool:
    return (
        name not in _NATIVE_RESOURCES
        and not name.startswith("hugepages-")
        and not name.startswith("kubernetes.io/")
        and "/" in name
    )


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


def pod_extended(pod: Mapping[str, Any]) -> dict[str, int]:
    """Extended resources (device plugins) the Pod takes, as the kubelet counts them."""
    spec = pod.get("spec", {})

    def of(container: Mapping[str, Any]) -> dict[str, int]:
        resources = container.get("resources") or {}
        amounts = {**(resources.get("requests") or {}), **(resources.get("limits") or {})}
        return {k: int(parse_quantity(v)) for k, v in amounts.items() if _is_extended(k)}

    total: dict[str, int] = defaultdict(int)
    for c in spec.get("containers", []):
        for name, count in of(c).items():
            total[name] += count
    for init in spec.get("initContainers") or []:
        for name, count in of(init).items():
            total[name] = max(total[name], count)
    return {k: v for k, v in total.items() if v}


def pod_devices(pod: Mapping[str, Any], annotation: str = ANNOTATION_DEVICES) -> dict[str, int]:
    """DRA driver → devices the Pod's claims ask for, as the session controller recorded them."""
    raw = (pod["metadata"].get("annotations") or {}).get(annotation)
    if not raw:
        return {}
    try:
        return {str(driver): int(count) for driver, count in json.loads(raw).items()}
    except (ValueError, AttributeError):
        return {}


def _pod_claims(
    pod: Mapping[str, Any], claims: Mapping[ClaimKey, Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    ns = pod["metadata"].get("namespace", "")
    out = []
    for ref in pod.get("spec", {}).get("resourceClaims") or []:
        name = ref.get("resourceClaimName")
        if name and (claim := claims.get((ns, name))) is not None:
            out.append(claim)
    return out


def _shares_of(request: Mapping[str, Any]) -> int | None:
    wanted = ((request.get("capacity") or {}).get("requests")) or {}
    for name in SHARES_CAPACITIES:
        if name in wanted:
            return int(parse_quantity(wanted[name]))
    return None


def _option(request: Mapping[str, Any]) -> ShareOption:
    return ShareOption(_shares_of(request), int(request.get("count") or 1))


def claim_share_requests(
    claim: Mapping[str, Any], fraction_classes: Mapping[str, str]
) -> ShareClaim:
    """The requests of a claim on fraction devices (`exactly` or `firstAvailable`)."""
    requests = []
    for request in ((claim.get("spec") or {}).get("devices") or {}).get("requests") or []:
        if (exactly := request.get("exactly")) is not None:
            subs = [exactly]
        else:
            subs = list(request.get("firstAvailable") or [])
        drivers = {fraction_classes.get(s.get("deviceClassName", "")) for s in subs}
        if not subs or len(drivers) != 1 or None in drivers:
            continue
        if any(s.get("allocationMode", "ExactCount") != "ExactCount" for s in subs):
            continue
        [driver] = drivers
        if driver is not None:
            requests.append(ShareRequest(driver, tuple(_option(s) for s in subs)))
    return tuple(requests)


def pod_share_claims(
    pod: Mapping[str, Any],
    claims: Mapping[ClaimKey, Mapping[str, Any]],
    profiles: Sequence[SlotProfile],
) -> tuple[ShareClaim, ...]:
    fraction = _fraction_classes(profiles)
    if not fraction:
        return ()
    out = []
    for claim in _pod_claims(pod, claims):
        if requests := claim_share_requests(claim, fraction):
            out.append(requests)
    return tuple(out)


def _fraction_classes(profiles: Sequence[SlotProfile]) -> dict[str, str]:
    return {p.device_class: p.driver for p in profiles if p.sharing_mode == _FRACTION}


def is_gated(pod: Mapping[str, Any]) -> bool:
    gates = pod.get("spec", {}).get("schedulingGates") or []
    return any(g.get("name") == SOKOVAN_GATE for g in gates)


def _phase(br: Mapping[str, Any]) -> str:
    return (br.get("status") or {}).get("phase") or BindRequestPhase.PENDING


def _live(br: Mapping[str, Any], live_uids: Mapping[PodKey, PodUid] | None) -> bool:
    """Whether a BindRequest is for the Pod that exists now under its name; a request of a
    replaced Pod (the controller recreated it) counts for nothing."""
    if live_uids is None:
        return True
    pod = (br["metadata"]["namespace"], br["spec"]["podName"])
    return live_uids.get(pod) == str(br["spec"].get("podUid"))


def live_pod_uids(pods: Iterable[Mapping[str, Any]]) -> dict[PodKey, PodUid]:
    return {_key(p): str(p["metadata"].get("uid", "")) for p in pods}


def in_flight_binds(
    bind_requests: Iterable[Mapping[str, Any]],
    live_uids: Mapping[PodKey, PodUid] | None = None,
) -> dict[PodUid, str]:
    """Pod uids with a BindRequest the binder has not failed → the node chosen for them."""
    binds = {}
    for br in bind_requests:
        if _phase(br) == BindRequestPhase.FAILED or not _live(br, live_uids):
            continue
        spec = br["spec"]
        binds[str(spec["podUid"])] = str(spec["selectedNode"])
    return binds


def bind_requested(bind_requests: Iterable[Mapping[str, Any]]) -> set[PodUid]:
    """Pod uids with any BindRequest: a failed one is placed again only once it is gone."""
    return {str(br["spec"]["podUid"]) for br in bind_requests}


def reserved_claims(
    bind_requests: Iterable[Mapping[str, Any]],
    live_uids: Mapping[PodKey, PodUid] | None = None,
) -> list[dict[str, Any]]:
    """Claim allocations of BindRequests that are pending or done for a live Pod: the
    allocator counts them until its informer shows them on the claims."""
    out = []
    for br in bind_requests:
        if _phase(br) == BindRequestPhase.FAILED or not _live(br, live_uids):
            continue
        ns = br["metadata"]["namespace"]
        for ca in br["spec"].get("resourceClaimAllocations") or []:
            out.append({"namespace": ns, "name": ca["name"], "allocation": ca["allocation"]})
    return out


def _key(pod: Mapping[str, Any]) -> PodKey:
    return pod["metadata"].get("namespace", ""), pod["metadata"]["name"]


def _awaits_sokovan(pod: Mapping[str, Any]) -> bool:
    spec = pod.get("spec", {})
    return not spec.get("nodeName") and (
        is_gated(pod) or spec.get("schedulerName") == SOKOVAN_SCHEDULER
    )


def target_node(pod: Mapping[str, Any], in_flight: Mapping[PodUid, str]) -> str | None:
    """The node a pod holds resources on: bound, chosen in a BindRequest, or released by
    sokovan and pinned."""
    spec = pod.get("spec", {})
    if spec.get("nodeName"):
        return str(spec["nodeName"])
    if (node := in_flight.get(str(pod["metadata"].get("uid", "")))) is not None:
        return node
    if _awaits_sokovan(pod):
        return None
    return (spec.get("nodeSelector") or {}).get(HOSTNAME_LABEL)


def holds_resources(pod: Mapping[str, Any]) -> bool:
    return pod.get("status", {}).get("phase") not in _ENDED_POD_PHASES


def is_dedicated(node: NodeState) -> bool:
    return any(
        t.key == DEDICATED_TAINT_KEY
        and t.value == DEDICATED_TAINT_VALUE
        and t.effect == "NoSchedule"
        for t in node.taints
    )


def _share_capacity(device: Mapping[str, Any]) -> int | None:
    capacity = device.get("capacity") or {}
    for name in SHARES_CAPACITIES:
        if name in capacity:
            return int(parse_quantity((capacity[name] or {}).get("value", 0)))
    return None


def _allocated(claim: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    allocation = (claim.get("status") or {}).get("allocation") or {}
    results: list[Mapping[str, Any]] = (allocation.get("devices") or {}).get("results") or []
    return results


def _consumed_shares(result: Mapping[str, Any]) -> int | None:
    consumed = result.get("consumedCapacity") or {}
    for name in SHARES_CAPACITIES:
        if name in consumed:
            return int(parse_quantity(consumed[name]))
    return None


def build_nodes(
    nodes: Iterable[Mapping[str, Any]],
    pods: Iterable[Mapping[str, Any]],
    resource_slices: Iterable[Mapping[str, Any]] = (),
    resource_claims: Iterable[Mapping[str, Any]] = (),
    in_flight: Mapping[PodUid, str] | None = None,
    profiles: Sequence[SlotProfile] = (),
    reserved: Iterable[Mapping[str, Any]] = (),
) -> list[NodeState]:
    in_flight = in_flight or {}
    pods = list(pods)
    claims = {
        (c["metadata"].get("namespace", ""), c["metadata"]["name"]): c for c in resource_claims
    }
    used: dict[str, Resources] = defaultdict(Resources)
    devices_used: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    extended_used: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    group_members: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for pod in pods:
        target = target_node(pod, in_flight)
        if target is not None and holds_resources(pod):
            used[target] = used[target] + pod_requests(pod)
            for driver, count in pod_devices(pod).items():
                devices_used[target][driver] += count
            for name, count in pod_extended(pod).items():
                extended_used[target][name] += count
            if (member := group_member_of(pod)) is not None:
                group_members[target][member[0]].add(member[1])
    devices: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    share_capacity: dict[str, dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
    # (driver, pool, device) → (node, slot, device key, shares capacity)
    index: dict[tuple[str, str, str], tuple[str, str, str, int | None]] = {}
    for rs in resource_slices:
        spec = rs.get("spec", {})
        if not spec.get("nodeName"):
            continue
        node, driver, pool = spec["nodeName"], spec["driver"], spec["pool"]["name"]
        for device in spec.get("devices") or []:
            slot = _slot_name(driver, device)
            devices[node][driver] += 1
            devices[node][f"{driver}/{slot}"] += 1
            device_key = f"{pool}/{device['name']}"
            capacity = _share_capacity(device)
            if capacity is not None:
                share_capacity[node][driver][device_key] = capacity
            index[driver, pool, device["name"]] = (node, slot, device_key, capacity)
    share_used: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    held: dict[ClaimKey, list[Mapping[str, Any]]] = {}
    for key, claim in claims.items():
        if results := _allocated(claim):
            held[key] = results
    for r in reserved:
        key = (r["namespace"], r["name"])
        if key not in held:
            held[key] = ((r.get("allocation") or {}).get("devices") or {}).get("results") or []
    for key, results in held.items():
        held_claim = claims.get(key)
        # Whole devices of Backend.AI sessions are counted from their Pods.
        ours = held_claim is not None and (
            (held_claim["metadata"].get("labels") or {}).get(LABEL_MANAGED_BY) == MANAGED_BY
        )
        for result in results:
            found = index.get((result["driver"], result["pool"], result["device"]))
            if found is None:
                continue
            node, slot, device_key, capacity = found
            if capacity is not None:
                consumed = _consumed_shares(result)
                share_used[node][result["driver"]][device_key] += (
                    consumed if consumed is not None and result.get("shareID") else capacity
                )
            elif not ours and not result.get("shareID"):
                devices_used[node][f"{result['driver']}/{slot}"] += 1
    states = []
    for node in nodes:
        meta, spec, status = node["metadata"], node.get("spec", {}), node.get("status", {})
        alloc = status.get("allocatable", {})
        conditions = status.get("conditions") or []
        ready = any(c.get("type") == "Ready" and c.get("status") == "True" for c in conditions)
        recycling = any(
            c.get("type") == NEEDS_RECYCLE_CONDITION and c.get("status") == "True"
            for c in conditions
        )
        name = meta["name"]
        states.append(
            NodeState(
                name=name,
                allocatable=Resources(
                    _milli(alloc.get("cpu", "0")),
                    _bytes(alloc.get("memory", "0")),
                    int(alloc.get("pods", "110")),
                ),
                used=used[name],
                labels=meta.get("labels") or {},
                taints=[
                    Taint(t["key"], t.get("value"), t["effect"]) for t in spec.get("taints") or []
                ],
                schedulable=ready and not recycling and not spec.get("unschedulable", False),
                devices=dict(devices[name]),
                devices_used=dict(devices_used[name]),
                extended={k: int(parse_quantity(v)) for k, v in alloc.items() if _is_extended(k)},
                extended_used=dict(extended_used[name]),
                share_capacity={d: dict(v) for d, v in share_capacity[name].items()},
                share_used={d: dict(v) for d, v in share_used[name].items()},
                group_members={g: frozenset(v) for g, v in group_members[name].items()},
            )
        )
    # Shares of session claims not allocated yet land where the allocator would put them.
    by_name = {s.name: s for s in states}
    for pod in pods:
        target = target_node(pod, in_flight)
        if target is None or target not in by_name or not holds_resources(pod):
            continue
        ns = pod["metadata"].get("namespace", "")
        pending = [c for c in _pod_claims(pod, claims) if (ns, c["metadata"]["name"]) not in held]
        share_claims = pod_share_claims(
            pod, {(ns, c["metadata"]["name"]): c for c in pending}, profiles
        )
        if share_claims and (take := by_name[target].fit_shares(share_claims)) is not None:
            by_name[target].take_shares(take)
    return states


def _slot_name(driver: str, device: Mapping[str, Any]) -> str:
    """bai-dra devices carry the Backend.AI slot they serve; others go by driver."""
    attribute = (device.get("attributes") or {}).get("slotName") or {}
    return str(attribute.get("string") or driver)


def is_sokovan_session(workload: Mapping[str, Any]) -> bool:
    scheduler = (workload.get("spec") or {}).get("schedulerName", SOKOVAN_SCHEDULER)
    return str(scheduler) == SOKOVAN_SCHEDULER


def session_index(workloads: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], str]:
    """The sokovan SessionWorkloads by namespace and session id."""
    return {
        (w["metadata"]["namespace"], str(w["spec"]["sessionId"])): w["metadata"]["name"]
        for w in workloads
        if is_sokovan_session(w) and (w.get("spec") or {}).get("sessionId")
    }


def session_of(pod: Mapping[str, Any], sessions: SessionIndex) -> str | None:
    """The sokovan SessionWorkload a kernel Pod belongs to, by its session label."""
    meta = pod["metadata"]
    labels = meta.get("labels") or {}
    if labels.get(LABEL_MANAGED_BY) != MANAGED_BY or LABEL_SESSION_ID not in labels:
        return None
    return sessions.get((meta.get("namespace", ""), labels[LABEL_SESSION_ID]))


def group_member_of(pod: Mapping[str, Any]) -> tuple[str, str] | None:
    """(SessionGroup id, session id) of a kernel Pod in a SessionGroup."""
    labels = pod["metadata"].get("labels") or {}
    if labels.get(LABEL_MANAGED_BY) != MANAGED_BY:
        return None
    group, session = labels.get(LABEL_SESSION_GROUP), labels.get(LABEL_SESSION_ID)
    if not group or not session:
        return None
    return str(group), str(session)


def session_group_of(spec: Mapping[str, Any]) -> GroupPolicy | None:
    """The SessionGroup policy of a SessionWorkload spec; None without a valid one."""
    raw = spec.get("sessionGroup")
    if not raw:
        return None
    try:
        group = SessionGroupSpec.model_validate(raw)
    except ValidationError:
        return None
    return GroupPolicy(
        id=group.id,
        direction=group.direction,
        enforcement=group.enforcement,
        admission=group.admission,
        member_count=group.member_count,
    )


def required_levels(spec: Mapping[str, Any]) -> list[str]:
    """A single-node session keeps all its kernels on one node, as on one Agent."""
    single = spec.get("clusterMode", "single-node") == "single-node"
    return [HOSTNAME_LABEL] if single and len(spec.get("kernels") or []) > 1 else []


def placement_of(workload: Mapping[str, Any]) -> Mapping[str, Any]:
    placement: Mapping[str, Any] = (workload.get("status") or {}).get("placement") or {}
    return placement


def build_pending_groups(
    workloads: Iterable[Mapping[str, Any]],
    pods: Iterable[Mapping[str, Any]],
    in_flight: Mapping[PodUid, str] | None = None,
    has_bind_request: Collection[PodUid] = (),
    resource_claims: Iterable[Mapping[str, Any]] = (),
    profiles: Sequence[SlotProfile] = (),
) -> list[PendingGroup]:
    """One gang per sokovan SessionWorkload with kernel Pods waiting: its members are the
    session's kernels, its order and topology come from the SessionWorkload."""
    in_flight = in_flight or {}
    workloads = list(workloads)
    sessions = session_index(workloads)
    claims = {
        (c["metadata"].get("namespace", ""), c["metadata"]["name"]): c for c in resource_claims
    }
    gated: dict[SessionKey, list[PendingPod]] = defaultdict(list)
    placed: dict[SessionKey, list[str]] = defaultdict(list)
    present: dict[SessionKey, int] = defaultdict(int)
    for pod in pods:
        meta = pod["metadata"]
        session = session_of(pod, sessions)
        if session is None or meta.get("deletionTimestamp") or not holds_resources(pod):
            continue
        key = (meta["namespace"], session)
        present[key] += 1
        if (node := target_node(pod, in_flight)) is not None:
            placed[key].append(node)
            continue
        if not _awaits_sokovan(pod) or str(meta.get("uid", "")) in has_bind_request:
            continue
        spec = pod.get("spec", {})
        gated[key].append(
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
                extended=pod_extended(pod),
                share_claims=pod_share_claims(pod, claims, profiles),
            )
        )
    # Per all_or_none SessionGroup: its sessions whose every kernel Pod exists
    ready: dict[str, int] = defaultdict(int)
    for workload in workloads:
        meta, spec = workload["metadata"], workload.get("spec") or {}
        group = session_group_of(spec)
        if (
            group is not None
            and group.all_or_none
            and is_sokovan_session(workload)
            and not meta.get("deletionTimestamp")
            and (workload.get("status") or {}).get("phase") not in _UNPLACEABLE_PHASES
            and present[meta["namespace"], meta["name"]] >= len(spec.get("kernels") or [])
        ):
            ready[group.id] += 1
    groups = []
    for workload in workloads:
        meta, spec = workload["metadata"], workload.get("spec") or {}
        key = (meta["namespace"], meta["name"])
        phase = (workload.get("status") or {}).get("phase")
        group = session_group_of(spec)
        # A placed session whose Pods wait again lost a member's bind (binder failure,
        # timeout): only the missing members are placed.
        if key not in gated or meta.get("deletionTimestamp") or phase in _UNPLACEABLE_PHASES:
            continue
        groups.append(
            PendingGroup(
                namespace=meta["namespace"],
                name=meta["name"],
                priority=int(spec.get("priority") or 0),
                created_at=str(meta.get("creationTimestamp", "")),
                min_member=len(spec.get("kernels") or []),
                pods=gated[key],
                required_levels=required_levels(spec),
                placed_members=len(placed[key]),
                placed_nodes=sorted(set(placed[key])),
                session_id=spec.get("sessionId"),
                session_group=group,
                group_ready=ready[group.id] if group is not None else 0,
            )
        )
    return groups


def newly_bound(
    workloads: Iterable[Mapping[str, Any]], pods: Iterable[Mapping[str, Any]]
) -> list[tuple[Mapping[str, Any], int]]:
    """Placed sessions whose every kernel Pod is bound to a node now, with their kernel count."""
    workloads = list(workloads)
    sessions = session_index(workloads)
    bound: dict[SessionKey, int] = defaultdict(int)
    for pod in pods:
        session = session_of(pod, sessions)
        if session is not None and pod.get("spec", {}).get("nodeName"):
            bound[pod["metadata"]["namespace"], session] += 1
    out = []
    for workload in workloads:
        meta, spec = workload["metadata"], workload.get("spec") or {}
        key = (meta["namespace"], meta["name"])
        kernels = len(spec.get("kernels") or [])
        if (
            placement_of(workload).get("phase") == PlacementPhase.PLACED
            and kernels
            and bound[key] >= kernels
        ):
            out.append((workload, kernels))
    return out
