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

from ai.backend.kube.controller.naming import HOSTNAME_LABEL, SOKOVAN_GATE
from ai.backend.kube.crd.base import CRD_VERSION
from ai.backend.kube.crd.scheduling import (
    BindRequest,
    BindRequestPhase,
    PodGroup,
    PodGroupPhase,
    Queue,
    SokovanBindMode,
)
from ai.backend.kube.scheduler.cycle import (
    Placement,
    PlacementStrategy,
    Skip,
    SkipReason,
    schedule,
)
from ai.backend.kube.scheduler.snapshot import (
    PodKey,
    build_nodes,
    build_pending_groups,
    build_queues,
    in_flight_binds,
)
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_MERGE_PATCH: Final = "application/merge-patch+json"
_JSON_PATCH: Final = "application/json-patch+json"
_PG = PodGroup.crd
_Q = Queue.crd
_BR = BindRequest.crd
_BIND_BACKOFF_LIMIT: Final = 3
BIND_TIMEOUT: Final = 60.0  # seconds a BindRequest may stay pending
_DRA_GROUP: Final = "resource.k8s.io"
_DRA_VERSION: Final = "v1"


class SokovanScheduler:
    _api: client.ApiClient
    _core: client.CoreV1Api
    _custom: client.CustomObjectsApi
    _interval: float
    _strategy: PlacementStrategy
    _bind_mode: SokovanBindMode
    _allocator_url: str

    def __init__(
        self,
        api: client.ApiClient,
        *,
        interval: float = 2.0,
        strategy: PlacementStrategy = PlacementStrategy.CONCENTRATED,
        bind_mode: SokovanBindMode = SokovanBindMode.GATE,
        allocator_url: str = "http://127.0.0.1:8786",
    ) -> None:
        self._api = api
        self._core = client.CoreV1Api(api)
        self._custom = client.CustomObjectsApi(api)
        self._interval = interval
        self._strategy = strategy
        self._bind_mode = bind_mode
        self._allocator_url = allocator_url

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
            queues_raw,
            slices_raw,
            claims_raw,
            binds_raw,
        ) = await asyncio.gather(
            self._core.list_node(),
            self._core.list_pod_for_all_namespaces(),
            self._custom.list_cluster_custom_object(_PG.group, CRD_VERSION, _PG.plural),
            self._custom.list_cluster_custom_object(_Q.group, CRD_VERSION, _Q.plural),
            self._custom.list_cluster_custom_object(_DRA_GROUP, _DRA_VERSION, "resourceslices"),
            self._custom.list_cluster_custom_object(_DRA_GROUP, _DRA_VERSION, "resourceclaims"),
            self._custom.list_cluster_custom_object(_BR.group, CRD_VERSION, _BR.plural),
        )
        await self._drop_failed_binds(binds_raw["items"])
        in_flight = in_flight_binds(binds_raw["items"])
        nodes = [self._api.sanitize_for_serialization(n) for n in nodes_raw.items]
        pods = [self._api.sanitize_for_serialization(p) for p in pods_raw.items]
        pending = build_pending_groups(groups_raw["items"], pods, in_flight)
        if not pending:
            return
        results = schedule(
            build_nodes(nodes, pods, slices_raw["items"], claims_raw["items"], in_flight),
            build_queues(queues_raw["items"], pods, in_flight),
            pending,
            self._strategy,
        )
        if self._bind_mode == SokovanBindMode.BINDER:
            results = await self._bind(results, pods, binds_raw["items"])
        placed = sum(isinstance(r, Placement) for r in results)
        log.debug("scheduling cycle done", pending_groups=len(pending), placed_groups=placed)
        current = {
            (g["metadata"]["namespace"], g["metadata"]["name"]): g for g in groups_raw["items"]
        }
        for result in results:
            key = (result.group.namespace, result.group.name)
            if isinstance(result, Placement) and self._bind_mode == SokovanBindMode.GATE:
                await self._release(result)
            await self._report(result, current.get(key))

    async def _drop_failed_binds(self, bind_requests: Sequence[Mapping[str, Any]]) -> None:
        """Requests the binder gave up on, or left pending too long (the binder is down);
        deleting them puts their Pods back in the queue."""
        now = datetime.now(UTC)
        for br in bind_requests:
            phase = (br.get("status") or {}).get("phase") or BindRequestPhase.PENDING
            meta = br["metadata"]
            created = datetime.fromisoformat(meta["creationTimestamp"])
            stale = (
                phase == BindRequestPhase.PENDING and (now - created).total_seconds() > BIND_TIMEOUT
            )
            if phase != BindRequestPhase.FAILED and not stale:
                continue
            log.trace(
                "bind request dropped",
                k8s_namespace=meta["namespace"],
                pod_name=br["spec"]["podName"],
                reason=(br.get("status") or {}).get("reason") or "bind timeout",
            )
            try:
                await self._custom.delete_namespaced_custom_object(
                    _BR.group, CRD_VERSION, meta["namespace"], _BR.plural, meta["name"]
                )
            except ApiException as e:
                if e.status != 404:
                    raise

    async def _bind(
        self,
        results: Sequence[Placement | Skip],
        pods: Sequence[Mapping[str, Any]],
        bind_requests: Sequence[Mapping[str, Any]],
    ) -> list[Placement | Skip]:
        """Allocate each placed group's claims and write its BindRequests; a group whose
        devices do not fit after all is skipped."""
        by_key: dict[PodKey, Mapping[str, Any]] = {
            (p["metadata"]["namespace"], p["metadata"]["name"]): p for p in pods
        }
        reserved = [
            r
            for br in bind_requests
            if (br.get("status") or {}).get("phase") in (None, BindRequestPhase.PENDING)
            for ca in br["spec"].get("resourceClaimAllocations") or []
            for r in ca["allocation"]["devices"]["results"]
        ]
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
                        r for ca in allocations for r in ca["allocation"]["devices"]["results"]
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
                "name": meta["name"],
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
        await self._custom.create_namespaced_custom_object(
            _BR.group, CRD_VERSION, meta["namespace"], _BR.plural, body
        )

    async def _release(self, placement: Placement) -> None:
        for pod_name, node in placement.nodes.items():
            pod = await self._core.read_namespaced_pod(pod_name, placement.group.namespace)
            gates = [
                {"name": g.name} for g in pod.spec.scheduling_gates or [] if g.name != SOKOVAN_GATE
            ]
            patch = [
                {
                    "op": "add",
                    "path": f"/spec/nodeSelector/{HOSTNAME_LABEL.replace('/', '~1')}",
                    "value": node,
                },
                {"op": "replace", "path": "/spec/schedulingGates", "value": gates},
            ]
            if pod.spec.node_selector is None:
                patch[0] = {
                    "op": "add",
                    "path": "/spec/nodeSelector",
                    "value": {HOSTNAME_LABEL: node},
                }
            await self._core.patch_namespaced_pod(
                pod_name, placement.group.namespace, patch, _content_type=_JSON_PATCH
            )
        log.trace(
            "pod group released",
            k8s_namespace=placement.group.namespace,
            pod_group=placement.group.name,
            nodes=",".join(sorted(set(placement.nodes.values()))),
        )

    async def _report(self, result: Placement | Skip, current: dict[str, Any] | None) -> None:
        now = datetime.now(UTC).isoformat()
        if isinstance(result, Placement):
            status: dict[str, Any] = {
                "phase": PodGroupPhase.SCHEDULED,
                "scheduled": len(result.nodes),
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
