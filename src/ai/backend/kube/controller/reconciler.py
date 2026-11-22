from __future__ import annotations

import base64
import json
import logging
from collections.abc import Mapping
from typing import Any, Final

from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.kube.controller.adapters import SokovanAdapter, pod_pending_reason
from ai.backend.kube.controller.devices import (
    DeviceClaim,
    build_resource_claim,
    device_slots,
    translate,
)
from ai.backend.kube.controller.manifests import (
    ControllerSettings,
    SessionSecrets,
    build_kernel_pod,
    build_kernel_secret,
    build_pod_group,
    build_session_network_policy,
    build_session_service,
    owner_reference,
    scheduler_adapter,
)
from ai.backend.kube.controller.naming import FINALIZER, LABEL_SESSION_ID
from ai.backend.kube.controller.reporter import StatusReporter
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
from ai.backend.kube.crd.scheduling import PodGroup
from ai.backend.kube.crd.session import (
    KernelStatus,
    SessionPhase,
    SessionWorkload,
    SessionWorkloadStatus,
)
from ai.backend.kube.crd.storage import StorageBinding
from ai.backend.kube.errors import InvalidSessionWorkloadError, UnsupportedBaseDistroError
from ai.backend.logging.structured import StructuredLogger, with_log_context

log = StructuredLogger(logging.getLogger(__spec__.name))

_MERGE_PATCH: Final = "application/merge-patch+json"
_SW = SessionWorkload.crd
_PG = PodGroup.crd
_SB = StorageBinding.crd
_DP = DeviceProfile.crd
_DRA_GROUP: Final = "resource.k8s.io"
_DRA_VERSION: Final = "v1"
_ENDED: Final = frozenset({SessionPhase.ERROR, SessionPhase.TERMINATED})
_EMPTY: Final = SessionWorkloadStatus()


class SessionReconciler:
    """Level-triggered: each call makes the cluster match one SessionWorkload."""

    _api: client.ApiClient
    _core: client.CoreV1Api
    _net: client.NetworkingV1Api
    _custom: client.CustomObjectsApi
    _settings: ControllerSettings
    _reporter: StatusReporter | None

    def __init__(
        self,
        api: client.ApiClient,
        settings: ControllerSettings,
        reporter: StatusReporter | None = None,
    ) -> None:
        self._api = api
        self._reporter = reporter
        self._core = client.CoreV1Api(api)
        self._net = client.NetworkingV1Api(api)
        self._custom = client.CustomObjectsApi(api)
        self._settings = settings

    async def reconcile(self, namespace: str, name: str) -> None:
        try:
            raw = await self._custom.get_namespaced_custom_object(
                _SW.group, CRD_VERSION, namespace, _SW.plural, name
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
                await self._patch_workload(
                    namespace,
                    name,
                    {
                        "metadata": {
                            "finalizers": [*raw["metadata"].get("finalizers", []), FINALIZER]
                        }
                    },
                )
            try:
                await self._ensure_children(workload)
            except (InvalidSessionWorkloadError, UnsupportedBaseDistroError) as e:
                log.trace("session workload rejected", reason=str(e.extra_msg))
                # The Manager learns it as kernels that failed to start, once.
                reported = {
                    k.kernel_id: k.reported_phase for k in (workload.status or _EMPTY).kernels
                }
                kernels = [
                    KernelStatus(
                        kernel_id=k.kernel_id,
                        phase=SessionPhase.ERROR,
                        reason="InvalidSpec",
                        message=e.extra_msg,
                        reported_phase=reported.get(k.kernel_id),
                    )
                    for k in workload.spec.kernels
                ]
                if self._reporter is not None:
                    kernels = await self._reporter.report(workload, kernels)
                await self._write_status(
                    workload,
                    SessionWorkloadStatus(
                        phase=SessionPhase.ERROR,
                        reason="InvalidSpec",
                        message=e.extra_msg,
                        observed_generation=raw["metadata"].get("generation"),
                        kernels=kernels,
                    ),
                )
                return
            await self._update_status(workload, deleting=False)

    async def _ensure_children(self, workload: SessionWorkload) -> None:
        ns = workload.metadata["namespace"]
        # Build every manifest first: an invalid spec creates nothing.
        secrets = await self._load_session_secrets(workload)
        scheduler_adapter(workload, self._settings).validate(workload)
        mounts = await self._resolve_mounts(workload)
        devices = await self._translate_devices(workload)
        kernel_objects = [
            (
                build_kernel_secret(workload, kernel, self._settings, secrets),
                build_kernel_pod(
                    workload,
                    kernel,
                    self._settings,
                    mounts[kernel.kernel_id],
                    devices[kernel.kernel_id],
                ),
                [
                    build_resource_claim(workload, kernel, c, owner_reference(workload))
                    for c in devices[kernel.kernel_id]
                ],
            )
            for kernel in workload.spec.kernels
        ]
        bindings = {binding_name(r.binding): r.binding for rs in mounts.values() for r in rs}
        for binding in bindings.values():
            await self._create(self._core.create_persistent_volume(build_volume(binding, ns)))
            await self._create(
                self._core.create_namespaced_persistent_volume_claim(ns, build_claim(binding, ns))
            )
        await self._create(
            self._core.create_namespaced_service(ns, build_session_service(workload))
        )
        await self._create(
            self._net.create_namespaced_network_policy(
                ns, build_session_network_policy(workload, self._settings)
            )
        )
        adapter = scheduler_adapter(workload, self._settings)
        if isinstance(adapter, SokovanAdapter):
            await self._create(
                self._custom.create_namespaced_custom_object(
                    _PG.group, CRD_VERSION, ns, _PG.plural, build_pod_group(workload)
                )
            )
        for obj in adapter.group_objects(workload):
            group, _, version = obj["apiVersion"].partition("/")
            await self._create(
                self._custom.create_namespaced_custom_object(
                    group, version, ns, _plural(obj["kind"]), obj
                )
            )
        started = _started_kernels(workload)
        for kernel, (secret, pod, claims) in zip(
            workload.spec.kernels, kernel_objects, strict=True
        ):
            if kernel.kernel_id in started:
                # A kernel Pod is never recreated, as a dead kernel container is not restarted.
                continue
            await self._create(self._core.create_namespaced_secret(ns, secret))
            for claim in claims:
                await self._create(
                    self._custom.create_namespaced_custom_object(
                        _DRA_GROUP, _DRA_VERSION, ns, "resourceclaims", claim
                    )
                )
            if await self._create(self._core.create_namespaced_pod(ns, pod)):
                log.debug("kernel pod created", pod_name=pod["metadata"]["name"])

    async def _resolve_mounts(self, workload: SessionWorkload) -> dict[str, list[ResolvedMount]]:
        if not any(kernel.mounts for kernel in workload.spec.kernels):
            return {kernel.kernel_id: [] for kernel in workload.spec.kernels}
        listed = await self._custom.list_cluster_custom_object(_SB.group, CRD_VERSION, _SB.plural)
        bindings = [StorageBinding.model_validate(item) for item in listed["items"]]
        return {
            kernel.kernel_id: [resolve_mount(m, bindings) for m in kernel.mounts]
            for kernel in workload.spec.kernels
        }

    async def _translate_devices(self, workload: SessionWorkload) -> dict[str, list[DeviceClaim]]:
        if not any(device_slots(k) for k in workload.spec.kernels):
            return {kernel.kernel_id: [] for kernel in workload.spec.kernels}
        listed = await self._custom.list_cluster_custom_object(_DP.group, CRD_VERSION, _DP.plural)
        profiles: dict[str, DeviceProfileSpec] = {}
        for item in listed["items"]:
            profile = DeviceProfile.model_validate(item)
            profiles[profile.spec.slot_name] = profile.spec
        return {kernel.kernel_id: translate(kernel, profiles) for kernel in workload.spec.kernels}

    async def _load_session_secrets(self, workload: SessionWorkload) -> SessionSecrets:
        if not workload.spec.secret_name:
            return SessionSecrets(None, {}, {})
        secret = await self._core.read_namespaced_secret(
            workload.spec.secret_name, workload.metadata["namespace"]
        )
        data = {k: _b64decode(v) for k, v in (secret.data or {}).items()}
        keypair = json.loads(data["cluster-ssh-keypair"]) if "cluster-ssh-keypair" in data else None
        internal: dict[str, Mapping[str, Any]] = {}
        bootstrap: dict[str, str] = {}
        for kernel in workload.spec.kernels:
            if (raw := data.get(f"kernel-{kernel.kernel_id}")) is None:
                continue
            entry = json.loads(raw)
            internal[kernel.kernel_id] = entry.get("internal_data") or {}
            if entry.get("bootstrap_script"):
                bootstrap[kernel.kernel_id] = entry["bootstrap_script"]
        return SessionSecrets(keypair, internal, bootstrap)

    async def _create(self, call: Any) -> bool:
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
        )
        return [self._api.sanitize_for_serialization(p) for p in pods.items]

    async def _update_status(self, workload: SessionWorkload, *, deleting: bool) -> int:
        pods = await self._session_pods(workload)
        by_kernel = {p["metadata"]["labels"].get("backend.ai/kernel-id"): p for p in pods}
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
            kernels = await self._reporter.report(workload, kernels)
        phase = session_phase(kernels, deleting)
        if deleting and not pods:
            phase = SessionPhase.TERMINATED
        failed = next((k for k in kernels if k.phase == SessionPhase.ERROR), None)
        reason, message = (failed.reason, failed.message) if failed else (None, None)
        if phase == SessionPhase.PENDING:
            reason, message = await self._pending_reason(workload, pods)
        await self._write_status(
            workload,
            SessionWorkloadStatus(
                phase=phase,
                reason=reason,
                message=message,
                observed_generation=workload.metadata.get("generation"),
                kernels=kernels,
            ),
        )
        return len(pods)

    async def _pending_reason(
        self, workload: SessionWorkload, pods: list[dict[str, Any]]
    ) -> tuple[str | None, str | None]:
        """Why the scheduler has not placed the session yet: sokovan's PodGroup, or the Pods."""
        if not isinstance(scheduler_adapter(workload, self._settings), SokovanAdapter):
            return pod_pending_reason(pods)
        try:
            group = await self._custom.get_namespaced_custom_object(
                _PG.group,
                CRD_VERSION,
                workload.metadata["namespace"],
                _PG.plural,
                workload.metadata["name"],
            )
        except ApiException as e:
            if e.status == 404:
                return None, None
            raise
        for cond in (group.get("status") or {}).get("conditions") or []:
            if cond.get("type") == "Scheduled" and cond.get("status") == "False":
                return cond.get("reason"), cond.get("message")
        return None, None

    async def _write_status(self, workload: SessionWorkload, status: SessionWorkloadStatus) -> None:
        current = (
            workload.status.model_dump(by_alias=True, mode="json") if workload.status else None
        )
        desired = status.model_dump(by_alias=True, mode="json")
        if current == desired:
            return
        if workload.status is None or workload.status.phase != status.phase:
            log.debug("session phase changed", phase=str(status.phase))
        await self._custom.patch_namespaced_custom_object_status(
            _SW.group,
            CRD_VERSION,
            workload.metadata["namespace"],
            _SW.plural,
            workload.metadata["name"],
            {"status": desired},
            _content_type=_MERGE_PATCH,
        )

    async def _finalize(self, workload: SessionWorkload, raw: Mapping[str, Any]) -> None:
        ns = workload.metadata["namespace"]
        finalizers = raw["metadata"].get("finalizers") or []
        if FINALIZER not in finalizers:
            return
        remaining = await self._update_status(workload, deleting=True)
        if remaining:
            if self._reporter is not None:
                await self._reporter.hand_over_logs(workload, await self._session_pods(workload))
            await self._core.delete_collection_namespaced_pod(
                ns,
                label_selector=f"{LABEL_SESSION_ID}={workload.spec.session_id}",
                grace_period_seconds=self._settings.termination_grace_seconds,
            )
            return
        log.debug("session pods gone; releasing finalizer")
        await self._patch_workload(
            ns,
            workload.metadata["name"],
            {"metadata": {"finalizers": [f for f in finalizers if f != FINALIZER]}},
        )

    async def _patch_workload(self, namespace: str, name: str, body: Mapping[str, Any]) -> None:
        await self._custom.patch_namespaced_custom_object(
            _SW.group, CRD_VERSION, namespace, _SW.plural, name, body, _content_type=_MERGE_PATCH
        )


def _started_kernels(workload: SessionWorkload) -> set[str]:
    """Kernels whose Pod has existed, as recorded in the status."""
    if workload.status is None:
        return set()
    return {k.kernel_id for k in workload.status.kernels if k.pod_uid is not None}


def _b64decode(value: str) -> str:
    return base64.b64decode(value).decode("utf-8")


def _plural(kind: str) -> str:
    return kind.lower() + "s"
