"""sokovan scheduler: place whole PodGroups, then start them in the configured bind mode.

Gate mode (Kueue form) releases the gate and pins each Pod; kube-scheduler binds. Binder mode
(KAI form) asks the DRA allocator sidecar for the claim allocations of the whole group and
writes a BindRequest per Pod; the binder records the claims and binds.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Final

import aiohttp
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.common.types import AgentSelectionStrategy
from ai.backend.kube.controller.naming import HOSTNAME_LABEL, SOKOVAN_GATE
from ai.backend.kube.crd.base import CRD_VERSION
from ai.backend.kube.crd.device import DeviceProfile, GPUAllocationPolicy
from ai.backend.kube.crd.scheduling import (
    BindRequest,
    BindRequestPhase,
    PodGroup,
    PodGroupPhase,
    SokovanBindMode,
)
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.kube.scheduler.cycle import (
    Placement,
    Skip,
    SkipReason,
    schedule,
)
from ai.backend.kube.scheduler.selection import NodeSelector
from ai.backend.kube.scheduler.snapshot import (
    PodKey,
    bind_requested,
    build_nodes,
    build_pending_groups,
    in_flight_binds,
    is_dedicated,
    is_gated,
    live_pod_uids,
    pod_group_of,
    reserved_claims,
    slot_profiles,
)
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_MERGE_PATCH: Final = "application/merge-patch+json"
_JSON_PATCH: Final = "application/json-patch+json"
_PG = PodGroup.crd
_BR = BindRequest.crd
_DP = DeviceProfile.crd
_SW = SessionWorkload.crd
# On a SessionWorkload: the scheduler asks the session controller to recreate its Pods.
ANNOTATION_REQUEUE: Final = "sokovan.backend.ai/requeue"
# Seconds before the scheduler asks again for the same gang.
REQUEUE_COOLDOWN: Final = 120.0
_BIND_BACKOFF_LIMIT: Final = 3
BIND_TIMEOUT: Final = 60.0  # seconds a BindRequest may stay pending
# Seconds a released Pod may stay unschedulable for kube-scheduler (gate mode).
RELEASE_TIMEOUT: Final = 120.0
# Seconds a gang may stay partly placed while its missing members do not fit.
STALE_GANG_TIMEOUT: Final = 300.0
_DRA_GROUP: Final = "resource.k8s.io"
_DRA_VERSION: Final = "v1"
_MAX_NAME: Final = 253

type GroupKey = tuple[str, str]  # namespace, PodGroup name


def _devices_of(allocation: Mapping[str, Any]) -> list[tuple[str, str, str, str]]:
    results = (allocation.get("devices") or {}).get("results") or []
    return sorted(
        (r["driver"], r["pool"], r["device"], str(r.get("shareID") or "")) for r in results
    )


def rolled_back(
    br: Mapping[str, Any],
    pods: Mapping[PodKey, Mapping[str, Any]],
    claims: Mapping[tuple[str, str], Mapping[str, Any]],
) -> bool:
    """Whether a failed BindRequest left nothing behind: its Pod is bound as asked, or none
    of its claims still holds its allocation for the Pod."""
    ns, spec = br["metadata"]["namespace"], br["spec"]
    pod = pods.get((ns, spec["podName"]))
    if (
        pod is not None
        and pod["metadata"].get("uid") == spec["podUid"]
        and pod.get("spec", {}).get("nodeName") == spec["selectedNode"]
    ):
        return True
    for ca in spec.get("resourceClaimAllocations") or []:
        claim = claims.get((ns, ca["name"]))
        if claim is None:
            continue
        status = claim.get("status") or {}
        allocation = status.get("allocation")
        reserved = {r.get("uid") for r in status.get("reservedFor") or []}
        if (
            allocation
            and _devices_of(allocation) == _devices_of(ca["allocation"])
            and (spec["podUid"] in reserved or not reserved)
        ):
            return False
    return True


def unplaceable_since(pod: Mapping[str, Any]) -> datetime | None:
    """When kube-scheduler found no node for a Pod sokovan released, if it has not placed it."""
    spec, meta = pod.get("spec", {}), pod["metadata"]
    if spec.get("nodeName") or is_gated(pod) or meta.get("deletionTimestamp"):
        return None
    if HOSTNAME_LABEL not in (spec.get("nodeSelector") or {}):
        return None
    for cond in (pod.get("status") or {}).get("conditions") or []:
        if (
            cond.get("type") == "PodScheduled"
            and cond.get("status") == "False"
            and cond.get("reason") == "Unschedulable"
            and cond.get("lastTransitionTime")
        ):
            return datetime.fromisoformat(cond["lastTransitionTime"])
    return None


def bind_request_name(pod: Mapping[str, Any]) -> str:
    """One BindRequest name per Pod uid: a Pod recreated under the same name while the request
    of its predecessor still exists gets its own."""
    meta = pod["metadata"]
    suffix = "-" + str(meta["uid"])[:8]
    return str(meta["name"])[: _MAX_NAME - len(suffix)] + suffix


def _rfc3339(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _workload_owners(pod: Mapping[str, Any]) -> list[str]:
    return [
        str(ref["name"])
        for ref in pod["metadata"].get("ownerReferences") or []
        if ref.get("kind") == _SW.kind
        and str(ref.get("apiVersion", "")).startswith(f"{_SW.group}/")
    ]


class SokovanScheduler:
    _api: client.ApiClient
    _core: client.CoreV1Api
    _custom: client.CustomObjectsApi
    _interval: float
    _selector: NodeSelector
    _bind_mode: SokovanBindMode
    _policy: GPUAllocationPolicy
    _allocator_url: str
    _stuck_since: dict[GroupKey, datetime]  # partly placed gangs whose rest does not fit
    _requeued: dict[GroupKey, datetime]  # gangs the controller was asked to recreate
    _workloads_denied: bool  # logged once that SessionWorkloads cannot be listed

    def __init__(
        self,
        api: client.ApiClient,
        *,
        interval: float = 2.0,
        strategy: AgentSelectionStrategy = AgentSelectionStrategy.CONCENTRATED,
        bind_mode: SokovanBindMode = SokovanBindMode.GATE,
        policy: GPUAllocationPolicy = GPUAllocationPolicy.DRA,
        allocator_url: str = "http://127.0.0.1:8786",
    ) -> None:
        self._api = api
        self._core = client.CoreV1Api(api)
        self._custom = client.CustomObjectsApi(api)
        self._interval = interval
        self._selector = NodeSelector(strategy)
        self._bind_mode = bind_mode
        self._policy = policy
        self._allocator_url = allocator_url
        self._stuck_since = {}
        self._requeued = {}
        self._workloads_denied = False

    async def run(self) -> None:
        while True:
            try:
                await self.cycle()
            except (ApiException, aiohttp.ClientError) as e:
                log.warning("scheduling cycle failed", exc_info=e)
            await asyncio.sleep(self._interval)

    async def cycle(self) -> None:
        (
            nodes_raw,
            pods_raw,
            groups_raw,
            workloads,
            slices_raw,
            claims_raw,
            binds_raw,
            profiles_raw,
        ) = await asyncio.gather(
            self._core.list_node(),
            self._core.list_pod_for_all_namespaces(),
            self._custom.list_cluster_custom_object(_PG.group, CRD_VERSION, _PG.plural),
            self._list_workloads(),
            self._custom.list_cluster_custom_object(_DRA_GROUP, _DRA_VERSION, "resourceslices"),
            self._custom.list_cluster_custom_object(_DRA_GROUP, _DRA_VERSION, "resourceclaims"),
            self._custom.list_cluster_custom_object(_BR.group, CRD_VERSION, _BR.plural),
            self._custom.list_cluster_custom_object(_DP.group, CRD_VERSION, _DP.plural),
        )
        now = datetime.now(UTC)
        pods = [self._api.sanitize_for_serialization(p) for p in pods_raw.items]
        claims: list[dict[str, Any]] = claims_raw["items"]
        binds: list[dict[str, Any]] = binds_raw["items"]
        await self._settle_failed_binds(binds, pods, claims, now)
        if self._bind_mode == SokovanBindMode.GATE:
            await self._recover_unplaceable(pods, now)
        profiles = slot_profiles(profiles_raw["items"])
        live = live_pod_uids(pods)
        in_flight = in_flight_binds(binds, live)
        reserved = reserved_claims(binds, live)
        pending = build_pending_groups(
            groups_raw["items"],
            pods,
            in_flight,
            bind_requested(binds),
            claims,
            profiles,
            workloads,
        )
        if not pending:
            self._stuck_since.clear()
            return
        nodes = build_nodes(
            [self._api.sanitize_for_serialization(n) for n in nodes_raw.items],
            pods,
            slices_raw["items"],
            claims,
            in_flight,
            profiles,
            reserved,
        )
        if self._bind_mode == SokovanBindMode.BINDER:
            # The binder bypasses kube-scheduler: sokovan owns only its dedicated nodes.
            nodes = [n for n in nodes if is_dedicated(n)]
        results = schedule(nodes, pending, self._selector, self._policy)
        if self._bind_mode == SokovanBindMode.BINDER:
            results = await self._bind(results, pods, reserved)
        else:
            results = await self._release_all(results)
        placed = sum(isinstance(r, Placement) for r in results)
        log.debug("scheduling cycle done", pending_groups=len(pending), placed_groups=placed)
        await self._tear_down_stale_gangs(results, pods, now)
        current = {
            (g["metadata"]["namespace"], g["metadata"]["name"]): g for g in groups_raw["items"]
        }
        for result in results:
            await self._report(result, current.get((result.group.namespace, result.group.name)))

    async def _list_workloads(self) -> list[dict[str, Any]]:
        """SessionWorkloads, for their creation time; without the right to list them the
        PodGroups' creation time orders the groups."""
        try:
            listed = await self._custom.list_cluster_custom_object(
                _SW.group, CRD_VERSION, _SW.plural
            )
        except ApiException as e:
            if e.status != 403:
                raise
            if not self._workloads_denied:
                log.warning("session workloads not listable; ordering by pod group age")
                self._workloads_denied = True
            return []
        items: list[dict[str, Any]] = listed["items"]
        return items

    async def _settle_failed_binds(
        self,
        bind_requests: Sequence[Mapping[str, Any]],
        pods: Sequence[Mapping[str, Any]],
        claims: Sequence[Mapping[str, Any]],
        now: datetime,
    ) -> None:
        """Fail requests left pending too long (the binder is down); delete failed ones once
        the binder rolled their claims back. A gang with no member bound gives up all its
        binds then, so it is placed again as a whole."""
        by_pod = {(p["metadata"]["namespace"], p["metadata"]["name"]): p for p in pods}
        by_claim = {(c["metadata"]["namespace"], c["metadata"]["name"]): c for c in claims}
        bound_groups = {
            (p["metadata"]["namespace"], group)
            for p in pods
            if p.get("spec", {}).get("nodeName") and (group := pod_group_of(p)) is not None
        }
        failed_groups: set[GroupKey] = set()
        for br in bind_requests:
            meta, spec = br["metadata"], br["spec"]
            phase = (br.get("status") or {}).get("phase") or BindRequestPhase.PENDING
            created = datetime.fromisoformat(meta["creationTimestamp"])
            if phase == BindRequestPhase.PENDING and (now - created).total_seconds() > BIND_TIMEOUT:
                await self._fail_bind(br, "bind timeout")
                phase = BindRequestPhase.FAILED
            if phase != BindRequestPhase.FAILED:
                continue
            if spec.get("podGroup"):
                failed_groups.add((meta["namespace"], spec["podGroup"]))
            if not rolled_back(br, by_pod, by_claim):
                continue  # the binder still has to free its claims
            log.trace(
                "bind request dropped",
                k8s_namespace=meta["namespace"],
                pod_name=spec["podName"],
                reason=(br.get("status") or {}).get("reason") or "bind timeout",
            )
            await self._delete_bind(br)
        for br in bind_requests:
            meta, spec = br["metadata"], br["spec"]
            key = (meta["namespace"], spec.get("podGroup") or "")
            phase = (br.get("status") or {}).get("phase") or BindRequestPhase.PENDING
            if (
                key in failed_groups
                and key not in bound_groups
                and phase == BindRequestPhase.PENDING
            ):
                await self._fail_bind(br, "another member of the gang failed to bind")

    async def _fail_bind(self, br: Mapping[str, Any], reason: str) -> None:
        """Mark a pending request failed unless the binder wrote its status meanwhile."""
        meta = br["metadata"]
        body = {
            "metadata": {"resourceVersion": meta["resourceVersion"]},
            "status": {"phase": BindRequestPhase.FAILED, "reason": reason},
        }
        try:
            await self._custom.patch_namespaced_custom_object_status(
                _BR.group,
                CRD_VERSION,
                meta["namespace"],
                _BR.plural,
                meta["name"],
                body,
                _content_type=_MERGE_PATCH,
            )
        except ApiException as e:
            if e.status not in (404, 409):
                raise

    async def _delete_bind(self, br: Mapping[str, Any]) -> None:
        meta = br["metadata"]
        try:
            await self._custom.delete_namespaced_custom_object(
                _BR.group, CRD_VERSION, meta["namespace"], _BR.plural, meta["name"]
            )
        except ApiException as e:
            if e.status != 404:
                raise

    async def _recover_unplaceable(self, pods: Sequence[Mapping[str, Any]], now: datetime) -> None:
        """A Pod sokovan released that kube-scheduler cannot place holds its gang forever: the
        gang is requeued: a gate cannot be put back on a Pod, so the controller recreates them."""
        stuck: set[GroupKey] = set()
        for pod in pods:
            group = pod_group_of(pod)
            since = unplaceable_since(pod)
            if group is None or since is None:
                continue
            if (now - since).total_seconds() > RELEASE_TIMEOUT:
                stuck.add((pod["metadata"]["namespace"], group))
        for namespace, group in sorted(stuck):
            await self._tear_down(
                namespace, group, pods, "kube-scheduler cannot place a member", now
            )

    async def _tear_down_stale_gangs(
        self, results: Sequence[Placement | Skip], pods: Sequence[Mapping[str, Any]], now: datetime
    ) -> None:
        stuck: set[GroupKey] = set()
        for result in results:
            group = result.group
            key = (group.namespace, group.name)
            if (
                isinstance(result, Skip)
                and result.reason in (SkipReason.UNSCHEDULABLE, SkipReason.RESERVED)
                and group.placed_members > 0
            ):
                stuck.add(key)
                since = self._stuck_since.setdefault(key, now)
                if (now - since).total_seconds() > STALE_GANG_TIMEOUT:
                    await self._tear_down(
                        group.namespace, group.name, pods, "missing members do not fit", now
                    )
        self._stuck_since = {k: v for k, v in self._stuck_since.items() if k in stuck}

    async def _tear_down(
        self,
        namespace: str,
        group: str,
        pods: Sequence[Mapping[str, Any]],
        reason: str,
        now: datetime,
    ) -> None:
        """Ask the session controller to recreate the gang: it deletes the remaining Pods and
        creates every kernel Pod and claim again, up to its retry limit."""
        key = (namespace, group)
        self._requeued = {
            k: at
            for k, at in self._requeued.items()
            if (now - at).total_seconds() < REQUEUE_COOLDOWN
        }
        last = self._requeued.get(key)
        if last is not None and (now - last).total_seconds() < REQUEUE_COOLDOWN:
            return  # requested already; the controller has not acted yet
        workload = next(
            (
                owner
                for p in pods
                if p["metadata"]["namespace"] == namespace and pod_group_of(p) == group
                for owner in _workload_owners(p)
            ),
            None,
        )
        if workload is None:
            log.warning(
                "pod group has no session workload to requeue",
                k8s_namespace=namespace,
                pod_group=group,
            )
            return
        body = {"metadata": {"annotations": {ANNOTATION_REQUEUE: _rfc3339(now)}}}
        try:
            await self._custom.patch_namespaced_custom_object(
                _SW.group,
                CRD_VERSION,
                namespace,
                _SW.plural,
                workload,
                body,
                _content_type=_MERGE_PATCH,
            )
        except ApiException as e:
            if e.status != 404:
                raise
            return
        self._requeued[key] = now
        self._stuck_since.pop(key, None)
        log.trace("pod group requeued", k8s_namespace=namespace, pod_group=group, reason=reason)

    async def _bind(
        self,
        results: Sequence[Placement | Skip],
        pods: Sequence[Mapping[str, Any]],
        reserved: list[dict[str, Any]],
    ) -> list[Placement | Skip]:
        """Allocate each placed group's claims and write its BindRequests; a group whose
        devices do not fit after all is skipped."""
        by_key: dict[PodKey, Mapping[str, Any]] = {
            (p["metadata"]["namespace"], p["metadata"]["name"]): p for p in pods
        }
        out: list[Placement | Skip] = []
        async with aiohttp.ClientSession() as http:
            for result in results:
                if not isinstance(result, Placement):
                    out.append(result)
                    continue
                ns = result.group.namespace
                claims_of = {
                    pod_name: [
                        {"namespace": ns, "name": c["resourceClaimName"]}
                        for c in by_key[ns, pod_name]["spec"].get("resourceClaims") or []
                        if c.get("resourceClaimName")
                    ]
                    for pod_name in result.nodes
                }
                if not any(claims_of.values()):
                    # No devices: the DRA allocator has nothing to decide (and may be down).
                    for pod_name, node in result.nodes.items():
                        await self._create_bind_request(
                            by_key[ns, pod_name], node, result.group.name, []
                        )
                    out.append(result)
                    continue
                request = {
                    "reserved": reserved,
                    "pods": [
                        {"name": pod_name, "node": node, "claims": claims_of[pod_name]}
                        for pod_name, node in result.nodes.items()
                    ],
                }
                try:
                    async with http.post(
                        f"{self._allocator_url}/v1/allocate", json=request
                    ) as resp:
                        resp.raise_for_status()
                        answer = await resp.json()
                except aiohttp.ClientError as e:
                    log.warning("DRA allocator unreachable", exc_info=e)
                    out.append(
                        Skip(result.group, SkipReason.UNSCHEDULABLE, "DRA allocator unavailable")
                    )
                    continue
                if not answer["fits"]:
                    out.append(Skip(result.group, SkipReason.UNSCHEDULABLE, answer["reason"]))
                    continue
                for pod_alloc in answer["pods"]:
                    pod = by_key[ns, pod_alloc["name"]]
                    allocations = pod_alloc.get("allocations") or []
                    await self._create_bind_request(
                        pod, result.nodes[pod_alloc["name"]], result.group.name, allocations
                    )
                    reserved += [
                        {"namespace": ns, "name": ca["name"], "allocation": ca["allocation"]}
                        for ca in allocations
                    ]
                out.append(result)
        return out

    async def _create_bind_request(
        self,
        pod: Mapping[str, Any],
        node: str,
        pod_group: str,
        allocations: Sequence[Mapping[str, Any]],
    ) -> None:
        meta = pod["metadata"]
        body = {
            "apiVersion": _BR.api_version,
            "kind": _BR.kind,
            "metadata": {
                "name": bind_request_name(pod),
                "namespace": meta["namespace"],
                # Gone with its Pod.
                "ownerReferences": [
                    {"apiVersion": "v1", "kind": "Pod", "name": meta["name"], "uid": meta["uid"]}
                ],
            },
            "spec": {
                "podName": meta["name"],
                "podUid": meta["uid"],
                "selectedNode": node,
                "podGroup": pod_group,
                "resourceClaimAllocations": list(allocations),
                "backoffLimit": _BIND_BACKOFF_LIMIT,
            },
        }
        try:
            await self._custom.create_namespaced_custom_object(
                _BR.group, CRD_VERSION, meta["namespace"], _BR.plural, body
            )
        except ApiException as e:
            if e.status != 409:
                raise
            # Written by an earlier cycle whose result this snapshot does not show yet.

    async def _release_all(self, results: Sequence[Placement | Skip]) -> list[Placement | Skip]:
        out: list[Placement | Skip] = []
        for result in results:
            if isinstance(result, Placement):
                out.append(await self._release(result))
            else:
                out.append(result)
        return out

    async def _release(self, placement: Placement) -> Placement | Skip:
        """Pin and ungate every Pod of the placement; nothing is patched unless every Pod
        still waits for sokovan."""
        ns = placement.group.namespace
        patches = []
        for pod_name, node in placement.nodes.items():
            try:
                pod = await self._core.read_namespaced_pod(pod_name, ns)
            except ApiException as e:
                if e.status != 404:
                    raise
                return Skip(placement.group, SkipReason.WAITING_FOR_PODS, f"pod {pod_name} is gone")
            gates = pod.spec.scheduling_gates or []
            if (
                pod.metadata.deletion_timestamp is not None
                or pod.spec.node_name
                or not any(g.name == SOKOVAN_GATE for g in gates)
            ):
                return Skip(
                    placement.group,
                    SkipReason.WAITING_FOR_PODS,
                    f"pod {pod_name} changed before its release",
                )
            selector = {"op": "add", "path": "/spec/nodeSelector", "value": {HOSTNAME_LABEL: node}}
            if pod.spec.node_selector is not None:
                selector = {
                    "op": "add",
                    "path": f"/spec/nodeSelector/{HOSTNAME_LABEL.replace('/', '~1')}",
                    "value": node,
                }
            remaining = [{"name": g.name} for g in gates if g.name != SOKOVAN_GATE]
            patches.append((
                pod_name,
                [selector, {"op": "replace", "path": "/spec/schedulingGates", "value": remaining}],
            ))
        for pod_name, patch in patches:
            await self._core.patch_namespaced_pod(pod_name, ns, patch, _content_type=_JSON_PATCH)
        log.trace(
            "pod group released",
            k8s_namespace=ns,
            pod_group=placement.group.name,
            nodes=",".join(sorted(set(placement.nodes.values()))),
        )
        return placement

    async def _report(self, result: Placement | Skip, current: dict[str, Any] | None) -> None:
        now = datetime.now(UTC).isoformat()
        if isinstance(result, Placement):
            status: dict[str, Any] = {
                "phase": PodGroupPhase.SCHEDULED,
                "scheduled": len(result.nodes) + result.group.placed_members,
                "lastSchedulingAttempt": now,
                "conditions": [
                    {
                        "type": "Scheduled",
                        "status": "True",
                        "reason": "Placed",
                        "lastTransitionTime": now,
                    }
                ],
            }
        else:
            previous = ((current or {}).get("status") or {}).get("conditions") or []
            if previous and previous[0].get("reason") == result.reason:
                return  # unchanged: avoid a write per cycle
            status = {
                "phase": PodGroupPhase.PENDING,
                "lastSchedulingAttempt": now,
                "conditions": [
                    {
                        "type": "Scheduled",
                        "status": "False",
                        "reason": str(result.reason),
                        "message": result.message,
                        "lastTransitionTime": now,
                    }
                ],
            }
        await self._custom.patch_namespaced_custom_object_status(
            _PG.group,
            CRD_VERSION,
            result.group.namespace,
            _PG.plural,
            result.group.name,
            {"status": status},
            _content_type=_MERGE_PATCH,
        )
