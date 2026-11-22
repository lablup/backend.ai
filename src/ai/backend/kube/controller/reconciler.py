from __future__ import annotations

import base64
import json
import logging
from collections.abc import Awaitable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final

import aiohttp
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.kube.controller.adapters import SokovanAdapter, pod_pending_reason
from ai.backend.kube.controller.cache import (
    DRA_GROUP,
    DRA_VERSION,
    ClusterKind,
    ClusterObjectCache,
    list_call,
)
from ai.backend.kube.controller.devices import (
    COMPUTE_DOMAIN_GROUP,
    COMPUTE_DOMAIN_PLURAL,
    COMPUTE_DOMAIN_VERSION,
    DeviceClaim,
    build_compute_domain,
    build_resource_claim,
    compute_domain_name,
    device_slots,
    needs_compute_domain,
    needs_share_pools,
    share_pools,
    translate,
)
from ai.backend.kube.controller.kernel_files import is_sudo_session
from ai.backend.kube.controller.manifests import (
    ControllerSettings,
    SessionSecrets,
    build_kernel_pod,
    build_kernel_secret,
    build_session_network_policy,
    build_session_service,
    owner_reference,
    scheduler_adapter,
)
from ai.backend.kube.controller.naming import (
    ANNOTATION_REQUEUE,
    FINALIZER,
    LABEL_KERNEL_ID,
    LABEL_SESSION_ID,
)
from ai.backend.kube.controller.reporter import Persist, StatusReporter
from ai.backend.kube.controller.status import kernel_status_from_pod, session_phase
from ai.backend.kube.controller.volumes import (
    ResolvedMount,
    binding_name,
    build_claim,
    build_volume,
    resolve_mount,
)
from ai.backend.kube.crd.base import CRD_VERSION
from ai.backend.kube.crd.device import DeviceProfile, DeviceProfileSpec
from ai.backend.kube.crd.session import (
    KernelStatus,
    PlacementPhase,
    SessionPhase,
    SessionWorkload,
    SessionWorkloadStatus,
)
from ai.backend.kube.crd.storage import StorageBinding
from ai.backend.kube.errors import InvalidSessionWorkloadError, UnsupportedBaseDistroError
from ai.backend.logging.structured import StructuredLogger, with_log_context

log = StructuredLogger(logging.getLogger(__spec__.name))

API_TIMEOUT: Final = 30.0
# A failure that is not the spec's (5xx, 403, 429, timeouts) ends the session after this many
# consecutive attempts, counted in the status.
MAX_TRANSIENT_FAILURES: Final = 5
# 403: a RoleBinding of a new session namespace not in effect yet; 429: API priority and fairness.
_TRANSIENT_CLIENT_ERRORS: Final = frozenset({403, 409, 429})
# Pods still there this long past their deletion grace are force-deleted when their node is
# NotReady or gone: no kubelet will ever confirm their end.
FORCE_DELETE_AFTER_SECONDS: Final = 60
# Requeues of one session before it ends in ERROR, counted apart for sokovan's requeues and
# for kubelet admission rejections.
MAX_REQUEUES: Final = 3
# Reported kernel phases of a kernel that has not started: its session may still be requeued.
_NOT_STARTED: Final = frozenset({None, SessionPhase.PENDING, SessionPhase.SCHEDULED})
# A Failed Pod with such a reason was rejected by the kubelet's admission (OutOfcpu, ...).
_ADMISSION_REJECTION_PREFIX: Final = "OutOf"
_MERGE_PATCH: Final = "application/merge-patch+json"
_JSON_PATCH: Final = "application/json-patch+json"
_SW = SessionWorkload.crd
_ENDED: Final = frozenset({SessionPhase.ERROR, SessionPhase.TERMINATED})
_ENDED_POD_PHASES: Final = frozenset({"Succeeded", "Failed"})
_EMPTY: Final = SessionWorkloadStatus()
# Status fields the sokovan scheduler writes; the controller never sends them.
_SCHEDULER_FIELDS: Final[set[str]] = {"placement"}
_PLACED: Final = frozenset({PlacementPhase.PLACED, PlacementPhase.BOUND})


@dataclass(frozen=True)
class _Requeue:
    annotation: str | None  # sokovan's annotation value; None for a kubelet admission rejection


class SessionReconciler:
    """Level-triggered: each call makes the cluster match one SessionWorkload."""

    _api: client.ApiClient
    _core: client.CoreV1Api
    _net: client.NetworkingV1Api
    _custom: client.CustomObjectsApi
    _settings: ControllerSettings
    _reporter: StatusReporter | None
    _cache: ClusterObjectCache | None

    def __init__(
        self,
        api: client.ApiClient,
        settings: ControllerSettings,
        reporter: StatusReporter | None = None,
        cache: ClusterObjectCache | None = None,
    ) -> None:
        self._api = api
        self._reporter = reporter
        self._core = client.CoreV1Api(api)
        self._net = client.NetworkingV1Api(api)
        self._custom = client.CustomObjectsApi(api)
        self._settings = settings
        self._cache = cache

    async def reconcile(self, namespace: str, name: str) -> None:
        try:
            raw = await self._custom.get_namespaced_custom_object(
                _SW.group, CRD_VERSION, namespace, _SW.plural, name, _request_timeout=API_TIMEOUT
            )
        except ApiException as e:
            if e.status == 404:
                return
            raise
        workload = SessionWorkload.model_validate(raw)
        with with_log_context(session_id=workload.spec.session_id, k8s_namespace=namespace):
            if raw["metadata"].get("deletionTimestamp"):
                await self._finalize(workload, raw)
                return
            if FINALIZER not in (raw["metadata"].get("finalizers") or []):
                await self._add_finalizer(raw)
            if workload.status is not None and workload.status.phase in _ENDED:
                # Nothing changes for an ended session until the Manager deletes it.
                return
            pods: list[dict[str, Any]] | None = await self._session_pods(workload)
            if not await self._handle_requeue(workload, raw, pods or []):
                return
            if self._needs_children(workload, raw):
                if not await self._try_ensure_children(workload, raw):
                    return
                pods = None
            await self._update_status(workload, deleting=False, pods=pods)

    def _requeue_request(
        self, workload: SessionWorkload, pods: list[dict[str, Any]]
    ) -> _Requeue | None:
        """A requeue not handled yet: sokovan's annotation with a value other than the last
        handled one, or a kubelet admission rejection of a kernel Pod while no kernel started.
        After a kernel started, a rejected Pod takes the ERROR path, so the Manager is told."""
        current = workload.status or _EMPTY
        requested = (workload.metadata.get("annotations") or {}).get(ANNOTATION_REQUEUE)
        if requested and requested != current.last_requeue:
            return _Requeue(requested)
        if current.requeuing:
            return None
        if any(k.reported_phase not in _NOT_STARTED for k in current.kernels):
            return None
        for pod in pods:
            if pod["metadata"].get("deletionTimestamp"):
                continue
            status = pod.get("status") or {}
            if status.get("phase") == "Failed" and str(status.get("reason") or "").startswith(
                _ADMISSION_REJECTION_PREFIX
            ):
                return _Requeue(None)
        return None

    async def _handle_requeue(
        self, workload: SessionWorkload, raw: Mapping[str, Any], pods: list[dict[str, Any]]
    ) -> bool:
        """Delete the kernel Pods, claims and ComputeDomain of a requeue and wait until they are
        gone; False while that is in progress or when the session ended."""
        current = workload.status or _EMPTY
        if (request := self._requeue_request(workload, pods)) is not None:
            update: dict[str, Any]
            if request.annotation is not None:
                count = current.requeue_count
                update = {"last_requeue": request.annotation, "requeue_count": count + 1}
                message = f"the session was requeued {count} times"
            else:
                count = current.admission_requeue_count
                update = {"admission_requeue_count": count + 1}
                message = f"kubelets rejected the session's Pods {count} times"
            if count >= MAX_REQUEUES:
                await self._fail(workload, raw, "RequeueLimitExceeded", message)
                return False
            log.debug("requeueing the session", requeue=request.annotation)
            # The kernels start over: no Pod is recorded, so none counts as deleted.
            kernels = [
                KernelStatus(kernel_id=k.kernel_id, reported_phase=k.reported_phase)
                for k in current.kernels
            ]
            await self._write_status(
                workload,
                current.model_copy(
                    update={
                        "phase": SessionPhase.PENDING,
                        "reason": "Requeued",
                        "message": None,
                        "kernels": kernels,
                        "requeuing": True,
                        **update,
                    }
                ),
            )
            current = workload.status or _EMPTY
        if not current.requeuing:
            return True
        ns = workload.metadata["namespace"]
        selector = f"{LABEL_SESSION_ID}={workload.spec.session_id}"
        if any(not p["metadata"].get("deletionTimestamp") for p in pods):
            await self._delete_kernel_pods(workload)
        else:
            # A Pod on a lost node never finishes terminating; the requeue must not wait forever.
            await self._force_delete_lost_pods(workload, pods)
        claims = await self._custom.list_namespaced_custom_object(
            DRA_GROUP,
            DRA_VERSION,
            ns,
            "resourceclaims",
            label_selector=selector,
            _request_timeout=API_TIMEOUT,
        )
        if claims["items"]:
            await self._custom.delete_collection_namespaced_custom_object(
                DRA_GROUP,
                DRA_VERSION,
                ns,
                "resourceclaims",
                label_selector=selector,
                _request_timeout=API_TIMEOUT,
            )
        domain_gone = True
        if await self._uses_compute_domain(workload):
            domain_gone = await self._delete_compute_domain(workload)
        if pods or claims["items"] or not domain_gone:
            return False
        await self._write_status(workload, current.model_copy(update={"requeuing": False}))
        return True

    async def _uses_compute_domain(self, workload: SessionWorkload) -> bool:
        if len(workload.spec.kernels) < 2:
            return False
        slots = {slot for k in workload.spec.kernels for slot in device_slots(k)}
        if not slots:
            return False
        for item in await self._cluster_items(ClusterKind.DEVICE_PROFILES):
            spec = DeviceProfile.model_validate(item).spec
            if spec.slot_name in slots and spec.compute_domain:
                return True
        return False

    async def _delete_compute_domain(self, workload: SessionWorkload) -> bool:
        """Start deleting the session's ComputeDomain; True once it is gone."""
        ns = workload.metadata["namespace"]
        name = compute_domain_name(workload)
        try:
            domain = await self._custom.get_namespaced_custom_object(
                COMPUTE_DOMAIN_GROUP,
                COMPUTE_DOMAIN_VERSION,
                ns,
                COMPUTE_DOMAIN_PLURAL,
                name,
                _request_timeout=API_TIMEOUT,
            )
            if not (domain.get("metadata") or {}).get("deletionTimestamp"):
                await self._custom.delete_namespaced_custom_object(
                    COMPUTE_DOMAIN_GROUP,
                    COMPUTE_DOMAIN_VERSION,
                    ns,
                    COMPUTE_DOMAIN_PLURAL,
                    name,
                    _request_timeout=API_TIMEOUT,
                )
        except ApiException as e:
            if e.status == 404:
                return True
            raise
        return False

    def _needs_children(self, workload: SessionWorkload, raw: Mapping[str, Any]) -> bool:
        """Whether a child object may be missing: a new generation or a kernel without a Pod."""
        status = workload.status
        if status is None or status.observed_generation != raw["metadata"].get("generation"):
            return True
        started = _started_kernels(workload)
        return any(k.kernel_id not in started for k in workload.spec.kernels)

    async def _try_ensure_children(self, workload: SessionWorkload, raw: Mapping[str, Any]) -> bool:
        """False when the session ended in ERROR instead. A transient failure is counted in the
        status and raised: the work queue retries it with backoff."""
        try:
            await self._ensure_children(workload)
        except (InvalidSessionWorkloadError, UnsupportedBaseDistroError) as e:
            log.trace("session workload rejected", reason=str(e.extra_msg))
            await self._fail(workload, raw, "InvalidSpec", str(e.extra_msg))
            return False
        except ApiException as e:
            if (
                e.status is not None
                and 400 <= e.status < 500
                and e.status not in _TRANSIENT_CLIENT_ERRORS
            ):
                await self._fail(workload, raw, "CreateFailed", f"{e.status} {e.reason}")
                return False
            if await self._transient_failure(workload, raw, f"{e.status} {e.reason}"):
                return False
            raise
        except (TimeoutError, aiohttp.ClientError) as e:
            if await self._transient_failure(workload, raw, repr(e)):
                return False
            raise
        current = workload.status or _EMPTY
        if current.transient_failures:
            await self._write_status(workload, current.model_copy(update={"transient_failures": 0}))
        return True

    async def _transient_failure(
        self, workload: SessionWorkload, raw: Mapping[str, Any], message: str
    ) -> bool:
        """Count a failure in the status; True when it ended the session in ERROR."""
        current = workload.status or _EMPTY
        count = current.transient_failures + 1
        if count >= MAX_TRANSIENT_FAILURES:
            await self._fail(workload, raw, "CreateFailed", message)
            return True
        await self._write_status(workload, current.model_copy(update={"transient_failures": count}))
        return False

    async def _fail(
        self, workload: SessionWorkload, raw: Mapping[str, Any], reason: str, message: str
    ) -> None:
        """The Manager learns it as kernels that failed to start, once."""
        previous = {k.kernel_id: k for k in (workload.status or _EMPTY).kernels}
        kernels = [
            KernelStatus(
                kernel_id=k.kernel_id,
                phase=SessionPhase.ERROR,
                reason=reason,
                message=message,
                reported_phase=previous[k.kernel_id].reported_phase
                if k.kernel_id in previous
                else None,
                pod_name=previous[k.kernel_id].pod_name if k.kernel_id in previous else None,
                pod_uid=previous[k.kernel_id].pod_uid if k.kernel_id in previous else None,
            )
            for k in workload.spec.kernels
        ]
        if self._reporter is not None:
            kernels = await self._reporter.report(
                workload, kernels, self._kernel_persister(workload, kernels)
            )
        await self._delete_kernel_pods(workload)
        await self._write_status(
            workload,
            SessionWorkloadStatus(
                phase=SessionPhase.ERROR,
                reason=reason,
                message=message,
                observed_generation=raw["metadata"].get("generation"),
                kernels=kernels,
                **_kept_fields(workload),
            ),
        )

    async def _ensure_children(self, workload: SessionWorkload) -> None:
        ns = workload.metadata["namespace"]
        t = {"_request_timeout": API_TIMEOUT}
        # Build every manifest first: an invalid spec creates nothing.
        secrets = await self._load_session_secrets(workload)
        scheduler_adapter(workload, self._settings).validate(workload)
        mounts = await self._resolve_mounts(workload)
        devices = await self._translate_devices(workload)
        compute_domain = needs_compute_domain(workload, devices)
        kernel_objects = [
            (
                build_kernel_secret(workload, kernel, self._settings, secrets),
                build_kernel_pod(
                    workload,
                    kernel,
                    self._settings,
                    mounts[kernel.kernel_id],
                    devices[kernel.kernel_id],
                    sudo_session=is_sudo_session(secrets.internal_data.get(kernel.kernel_id, {})),
                    compute_domain=compute_domain,
                ),
                [
                    build_resource_claim(workload, kernel, c, owner_reference(workload))
                    for c in devices[kernel.kernel_id]
                    if c.extended_resource is None
                ],
            )
            for kernel in workload.spec.kernels
        ]
        bindings = {binding_name(r.binding): r.binding for rs in mounts.values() for r in rs}
        for binding in bindings.values():
            await self._create(self._core.create_persistent_volume(build_volume(binding, ns), **t))
            await self._create(
                self._core.create_namespaced_persistent_volume_claim(
                    ns, build_claim(binding, ns), **t
                )
            )
        await self._create(
            self._core.create_namespaced_service(ns, build_session_service(workload), **t)
        )
        await self._create(
            self._net.create_namespaced_network_policy(
                ns, build_session_network_policy(workload, self._settings), **t
            )
        )
        adapter = scheduler_adapter(workload, self._settings)
        for obj in adapter.group_objects(workload):
            group, _, version = obj["apiVersion"].partition("/")
            await self._create(
                self._custom.create_namespaced_custom_object(
                    group, version, ns, _plural(obj["kind"]), obj, **t
                )
            )
        if compute_domain:
            await self._create(
                self._custom.create_namespaced_custom_object(
                    COMPUTE_DOMAIN_GROUP,
                    COMPUTE_DOMAIN_VERSION,
                    ns,
                    COMPUTE_DOMAIN_PLURAL,
                    build_compute_domain(workload, owner_reference(workload)),
                    **t,
                )
            )
        started = _started_kernels(workload)
        for kernel, (secret, pod, claims) in zip(
            workload.spec.kernels, kernel_objects, strict=True
        ):
            if kernel.kernel_id in started:
                # A kernel Pod is never recreated, as a dead kernel container is not restarted.
                continue
            await self._create(self._core.create_namespaced_secret(ns, secret, **t))
            for claim in claims:
                await self._create(
                    self._custom.create_namespaced_custom_object(
                        DRA_GROUP, DRA_VERSION, ns, "resourceclaims", claim, **t
                    )
                )
            if await self._create(self._core.create_namespaced_pod(ns, pod, **t)):
                log.debug("kernel pod created", pod_name=pod["metadata"]["name"])

    async def _cluster_items(self, kind: ClusterKind) -> list[dict[str, Any]]:
        if self._cache is not None:
            return await self._cache.items(kind)
        listed = await list_call(self._custom, kind)(_request_timeout=API_TIMEOUT)
        items: list[dict[str, Any]] = listed["items"]
        return items

    async def _resolve_mounts(self, workload: SessionWorkload) -> dict[str, list[ResolvedMount]]:
        if not any(kernel.mounts for kernel in workload.spec.kernels):
            return {kernel.kernel_id: [] for kernel in workload.spec.kernels}
        bindings = [
            StorageBinding.model_validate(item)
            for item in await self._cluster_items(ClusterKind.STORAGE_BINDINGS)
        ]
        return {
            kernel.kernel_id: [resolve_mount(m, bindings) for m in kernel.mounts]
            for kernel in workload.spec.kernels
        }

    async def _translate_devices(self, workload: SessionWorkload) -> dict[str, list[DeviceClaim]]:
        if not any(device_slots(k) for k in workload.spec.kernels):
            return {kernel.kernel_id: [] for kernel in workload.spec.kernels}
        profiles: dict[str, DeviceProfileSpec] = {}
        for item in await self._cluster_items(ClusterKind.DEVICE_PROFILES):
            profile = DeviceProfile.model_validate(item)
            profiles[profile.spec.slot_name] = profile.spec
        pools = {}
        if needs_share_pools(workload.spec.kernels, profiles):
            slices = await self._cluster_items(ClusterKind.RESOURCE_SLICES)
            pools = share_pools(slices, profiles.values())
        policy = self._settings.gpu_allocation_policy
        return {
            kernel.kernel_id: translate(kernel, profiles, policy, pools)
            for kernel in workload.spec.kernels
        }

    async def _load_session_secrets(self, workload: SessionWorkload) -> SessionSecrets:
        if not workload.spec.secret_name:
            return SessionSecrets(None, {}, {})
        secret = await self._core.read_namespaced_secret(
            workload.spec.secret_name, workload.metadata["namespace"], _request_timeout=API_TIMEOUT
        )
        try:
            data = {k: _b64decode(v) for k, v in (secret.data or {}).items()}
            keypair = (
                json.loads(data["cluster-ssh-keypair"]) if "cluster-ssh-keypair" in data else None
            )
            internal: dict[str, Mapping[str, Any]] = {}
            bootstrap: dict[str, str] = {}
            for kernel in workload.spec.kernels:
                if (raw := data.get(f"kernel-{kernel.kernel_id}")) is None:
                    continue
                entry = json.loads(raw)
                internal[kernel.kernel_id] = entry.get("internal_data") or {}
                if entry.get("bootstrap_script"):
                    bootstrap[kernel.kernel_id] = entry["bootstrap_script"]
        except (ValueError, AttributeError, TypeError) as e:
            raise InvalidSessionWorkloadError(
                f"session secret {workload.spec.secret_name} is malformed: {e}"
            ) from e
        return SessionSecrets(keypair, internal, bootstrap)

    async def _create(self, call: Awaitable[Any]) -> bool:
        """Await a create call; an existing object is fine (names are idempotent)."""
        try:
            await call
        except ApiException as e:
            if e.status == 409:
                return False
            raise
        return True

    async def _session_pods(self, workload: SessionWorkload) -> list[dict[str, Any]]:
        pods = await self._core.list_namespaced_pod(
            workload.metadata["namespace"],
            label_selector=f"{LABEL_SESSION_ID}={workload.spec.session_id}",
            _request_timeout=API_TIMEOUT,
        )
        return [self._api.sanitize_for_serialization(p) for p in pods.items]

    async def _update_status(
        self,
        workload: SessionWorkload,
        *,
        deleting: bool,
        pods: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Report the kernels' phases and record them; return the session's Pods."""
        if pods is None:
            pods = await self._session_pods(workload)
        by_kernel = {p["metadata"]["labels"].get(LABEL_KERNEL_ID): p for p in pods}
        previous = {k.kernel_id: k for k in workload.status.kernels} if workload.status else {}
        kernels = []
        for k in workload.spec.kernels:
            pod = by_kernel.get(k.kernel_id)
            status = kernel_status_from_pod(k.kernel_id, pod)
            last = previous.get(k.kernel_id)
            if last is not None:
                status.reported_phase = last.reported_phase
            if pod is None and last is not None and last.pod_uid is not None:
                # Keep the record of the Pod: it is how the kernel stays marked as started.
                status = last.model_copy()
                if not deleting and last.phase not in _ENDED:
                    status.phase = SessionPhase.ERROR
                    status.reason = "PodDeleted"
                    status.message = "The kernel Pod was deleted outside the session controller."
            if deleting and pod is None and status.phase not in _ENDED:
                status = status.model_copy(update={"phase": SessionPhase.TERMINATED})
            kernels.append(status)
        if self._reporter is not None:
            kernels = await self._reporter.report(
                workload, kernels, self._kernel_persister(workload, kernels), deleting=deleting
            )
        if not deleting:
            await self._delete_failed_pods(workload, kernels, by_kernel)
        phase = session_phase(kernels, deleting)
        if deleting and not pods:
            phase = SessionPhase.TERMINATED
        failed = next((k for k in kernels if k.phase == SessionPhase.ERROR), None)
        reason, message = (failed.reason, failed.message) if failed else (None, None)
        kept = _kept_fields(workload)
        if phase == SessionPhase.PENDING:
            reason, message = await self._pending_reason(workload, pods)
            reported = await self._report_placement_timeout(
                workload, kernels, pods, reason, message
            )
            if reported is not None:
                kept["placement_timeout_reported_at"] = reported
        await self._write_status(
            workload,
            SessionWorkloadStatus(
                phase=phase,
                reason=reason,
                message=message,
                observed_generation=workload.metadata.get("generation"),
                kernels=kernels,
                **kept,
            ),
        )
        return pods

    async def _report_placement_timeout(
        self,
        workload: SessionWorkload,
        kernels: list[KernelStatus],
        pods: list[dict[str, Any]],
        reason: str | None,
        message: str | None,
        now: datetime | None = None,
    ) -> str | None:
        """Hand an admitted session that stays unplaced back to the Manager (contract C11), once
        per placement attempt; return the report time. An attempt starts when its kernel Pods
        are created. The time is recorded right after the event: a restart resends at most once."""
        current = workload.status or _EMPTY
        if self._reporter is None or current.requeuing:
            return None
        if any(k.reported_phase not in _NOT_STARTED for k in kernels):
            return None
        live = [p for p in pods if not p["metadata"].get("deletionTimestamp")]
        if not live or all((p.get("spec") or {}).get("nodeName") for p in live):
            return None
        created = [
            _parse_time(p["metadata"]["creationTimestamp"])
            for p in live
            if p["metadata"].get("creationTimestamp")
        ]
        if created:
            attempt_started = min(created)
        elif workload.metadata.get("creationTimestamp"):
            attempt_started = _parse_time(workload.metadata["creationTimestamp"])
        else:
            return None
        now = now or datetime.now(UTC)
        if (now - attempt_started).total_seconds() < self._settings.placement_timeout_seconds:
            return None
        reported = _parse_rfc3339(current.placement_timeout_reported_at)
        if reported is not None and reported >= attempt_started:
            return None
        await self._reporter.report_placement_timeout(workload, reason or "Unschedulable", message)
        stamp = now.isoformat()
        await self._patch_status(workload, {"placementTimeoutReportedAt": stamp})
        workload.status = current.model_copy(update={"placement_timeout_reported_at": stamp})
        log.trace("placement timeout reported", reason=reason or "Unschedulable")
        return stamp

    def _kernel_persister(self, workload: SessionWorkload, kernels: list[KernelStatus]) -> Persist:
        """Records one kernel's `reportedPhase` (with the other kernels as computed) right after
        an event is sent, before the rest of the status is written."""
        current = list(kernels)

        async def persist(updated: KernelStatus) -> None:
            for idx, k in enumerate(current):
                if k.kernel_id == updated.kernel_id:
                    current[idx] = updated
            await self._patch_status(
                workload, {"kernels": [k.model_dump(by_alias=True, mode="json") for k in current]}
            )
            workload.status = (workload.status or _EMPTY).model_copy(
                update={"kernels": list(current)}
            )

        return persist

    async def _delete_failed_pods(
        self,
        workload: SessionWorkload,
        kernels: list[KernelStatus],
        by_kernel: Mapping[str | None, Mapping[str, Any]],
    ) -> None:
        """A kernel declared ERROR while its Pod still waits (a pull that never succeeds) gives
        its node back."""
        for k in kernels:
            pod = by_kernel.get(k.kernel_id)
            if k.phase != SessionPhase.ERROR or pod is None:
                continue
            if pod["metadata"].get("deletionTimestamp"):
                continue
            if (pod.get("status") or {}).get("phase") in _ENDED_POD_PHASES:
                continue
            await self._delete_pod(workload.metadata["namespace"], pod["metadata"]["name"])

    async def _delete_kernel_pods(self, workload: SessionWorkload) -> None:
        await self._core.delete_collection_namespaced_pod(
            workload.metadata["namespace"],
            label_selector=f"{LABEL_SESSION_ID}={workload.spec.session_id}",
            grace_period_seconds=self._settings.termination_grace_seconds,
            _request_timeout=API_TIMEOUT,
        )

    async def _delete_pod(self, namespace: str, name: str, grace: int | None = None) -> None:
        try:
            await self._core.delete_namespaced_pod(
                name, namespace, grace_period_seconds=grace, _request_timeout=API_TIMEOUT
            )
        except ApiException as e:
            if e.status != 404:
                raise

    async def _pending_reason(
        self, workload: SessionWorkload, pods: list[dict[str, Any]]
    ) -> tuple[str | None, str | None]:
        """Why the scheduler has not placed the session yet: sokovan's placement status, or
        the Pods."""
        if not isinstance(scheduler_adapter(workload, self._settings), SokovanAdapter):
            return pod_pending_reason(pods)
        placement = workload.status.placement if workload.status else None
        if placement is None or placement.phase in _PLACED:
            return None, None
        return placement.reason, placement.message

    async def _write_status(self, workload: SessionWorkload, status: SessionWorkloadStatus) -> None:
        """Write the status the controller owns; `placement` stays sokovan's."""
        current = (
            workload.status.model_dump(by_alias=True, mode="json", exclude=_SCHEDULER_FIELDS)
            if workload.status
            else None
        )
        desired = status.model_dump(by_alias=True, mode="json", exclude=_SCHEDULER_FIELDS)
        if current == desired:
            return
        if workload.status is None or workload.status.phase != status.phase:
            log.debug("session phase changed", phase=str(status.phase))
        await self._patch_status(workload, desired)
        placement = workload.status.placement if workload.status else None
        workload.status = status.model_copy(update={"placement": placement})

    async def _patch_status(self, workload: SessionWorkload, status: Mapping[str, Any]) -> None:
        await self._custom.patch_namespaced_custom_object_status(
            _SW.group,
            CRD_VERSION,
            workload.metadata["namespace"],
            _SW.plural,
            workload.metadata["name"],
            {"status": dict(status)},
            _content_type=_MERGE_PATCH,
            _request_timeout=API_TIMEOUT,
        )

    async def _finalize(self, workload: SessionWorkload, raw: Mapping[str, Any]) -> None:
        if FINALIZER not in (raw["metadata"].get("finalizers") or []):
            return
        pods = await self._update_status(workload, deleting=True)
        if pods:
            if any(not p["metadata"].get("deletionTimestamp") for p in pods):
                await self._delete_kernel_pods(workload)
            await self._force_delete_lost_pods(workload, pods)
            return
        log.debug("session pods gone; releasing finalizer")
        await self._remove_finalizer(raw)

    async def _force_delete_lost_pods(
        self,
        workload: SessionWorkload,
        pods: list[dict[str, Any]],
        now: datetime | None = None,
    ) -> None:
        """Pods whose node is NotReady or gone never finish terminating: past their deletion
        grace plus a margin, they are removed without waiting for a kubelet."""
        now = now or datetime.now(UTC)
        node_ready: dict[str, bool] = {}
        for pod in pods:
            if not (deleted := pod["metadata"].get("deletionTimestamp")):
                continue
            if now < _parse_time(deleted) + timedelta(seconds=FORCE_DELETE_AFTER_SECONDS):
                continue
            node = (pod.get("spec") or {}).get("nodeName")
            if node and node not in node_ready:
                node_ready[node] = await self._node_ready(node)
            if node and node_ready[node]:
                continue
            log.warning(
                "force-deleting a kernel pod on a lost node",
                pod_name=pod["metadata"]["name"],
                node_name=node,
            )
            await self._delete_pod(workload.metadata["namespace"], pod["metadata"]["name"], 0)

    async def _node_ready(self, name: str) -> bool:
        try:
            node = await self._core.read_node(name, _request_timeout=API_TIMEOUT)
        except ApiException as e:
            if e.status == 404:
                return False
            raise
        conditions = (node.status.conditions if node.status else None) or []
        return any(c.type == "Ready" and c.status == "True" for c in conditions)

    async def _add_finalizer(self, raw: Mapping[str, Any]) -> None:
        """A JSON patch that fails when another writer changed the finalizers meanwhile."""
        meta = raw["metadata"]
        finalizers = meta.get("finalizers")
        if finalizers:
            ops: list[dict[str, Any]] = [
                {"op": "test", "path": "/metadata/finalizers", "value": finalizers},
                {"op": "add", "path": "/metadata/finalizers/-", "value": FINALIZER},
            ]
        else:
            ops = [
                {
                    "op": "test",
                    "path": "/metadata/resourceVersion",
                    "value": meta["resourceVersion"],
                },
                {"op": "add", "path": "/metadata/finalizers", "value": [FINALIZER]},
            ]
        await self._json_patch(meta["namespace"], meta["name"], ops)

    async def _remove_finalizer(self, raw: Mapping[str, Any]) -> None:
        meta = raw["metadata"]
        idx = (meta.get("finalizers") or []).index(FINALIZER)
        await self._json_patch(
            meta["namespace"],
            meta["name"],
            [
                {"op": "test", "path": f"/metadata/finalizers/{idx}", "value": FINALIZER},
                {"op": "remove", "path": f"/metadata/finalizers/{idx}"},
            ],
        )

    async def _json_patch(self, namespace: str, name: str, ops: list[dict[str, Any]]) -> None:
        await self._custom.patch_namespaced_custom_object(
            _SW.group,
            CRD_VERSION,
            namespace,
            _SW.plural,
            name,
            ops,
            _content_type=_JSON_PATCH,
            _request_timeout=API_TIMEOUT,
        )


def _started_kernels(workload: SessionWorkload) -> set[str]:
    """Kernels whose Pod has existed, as recorded in the status."""
    if workload.status is None:
        return set()
    return {k.kernel_id for k in workload.status.kernels if k.pod_uid is not None}


def _kept_fields(workload: SessionWorkload) -> dict[str, Any]:
    """Status fields a rewrite of the kernels' status carries over."""
    status = workload.status or _EMPTY
    return {
        "last_requeue": status.last_requeue,
        "requeue_count": status.requeue_count,
        "admission_requeue_count": status.admission_requeue_count,
        "requeuing": status.requeuing,
        "transient_failures": status.transient_failures,
        "placement_timeout_reported_at": status.placement_timeout_reported_at,
    }


def _parse_rfc3339(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _parse_time(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=UTC)
    return datetime.fromisoformat(str(raw))


def _b64decode(value: str) -> str:
    return base64.b64decode(value).decode("utf-8")


def _plural(kind: str) -> str:
    return kind.lower() + "s"
