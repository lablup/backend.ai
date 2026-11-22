"""Derive kernel and session phases from Pods (suggestion 13.4)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from ai.backend.kube.controller.naming import KERNEL_CONTAINER, KRUNNER_CONTAINER
from ai.backend.kube.crd.session import KernelStatus, SessionPhase

# Waiting reasons that do not resolve without a change of spec.
FATAL_WAITING_REASONS: Final = frozenset({
    "ErrImagePull",
    "ImagePullBackOff",
    "InvalidImageName",
    "CreateContainerConfigError",
    "CreateContainerError",
    "CrashLoopBackOff",
})

_ORDER: Final = (
    SessionPhase.PENDING,
    SessionPhase.SCHEDULED,
    SessionPhase.PREPARING,
    SessionPhase.PULLING,
    SessionPhase.CREATING,
    SessionPhase.RUNNING,
)


def _container_status(pod: Mapping[str, Any], key: str, name: str) -> Mapping[str, Any] | None:
    statuses: list[Mapping[str, Any]] = pod.get("status", {}).get(key) or []
    return next((cs for cs in statuses if cs.get("name") == name), None)


def _condition(pod: Mapping[str, Any], type_: str) -> str | None:
    conditions: list[Mapping[str, str]] = pod.get("status", {}).get("conditions") or []
    return next((c.get("status") for c in conditions if c.get("type") == type_), None)


def kernel_status_from_pod(kernel_id: str, pod: Mapping[str, Any] | None) -> KernelStatus:
    if pod is None:
        return KernelStatus(kernel_id=kernel_id, phase=SessionPhase.PENDING)
    meta = pod["metadata"]
    status = pod.get("status", {})
    result = KernelStatus(
        kernel_id=kernel_id,
        pod_name=meta["name"],
        pod_uid=meta.get("uid"),
        node_name=pod.get("spec", {}).get("nodeName"),
        pod_ip=status.get("podIP"),
    )
    init = _container_status(pod, "initContainerStatuses", KRUNNER_CONTAINER)
    main = _container_status(pod, "containerStatuses", KERNEL_CONTAINER)
    if main is not None and main.get("containerID"):
        result.container_id = main["containerID"].split("://", 1)[-1]

    for cs in (init, main):
        if cs is None:
            continue
        waiting = cs.get("state", {}).get("waiting") or {}
        if waiting.get("reason") in FATAL_WAITING_REASONS:
            return _with(result, SessionPhase.ERROR, waiting["reason"], waiting.get("message"))
        terminated = cs.get("state", {}).get("terminated")
        if terminated is not None and (cs is main or terminated.get("exitCode", 0) != 0):
            result.exit_code = terminated.get("exitCode")
            phase = SessionPhase.TERMINATED if result.exit_code == 0 else SessionPhase.ERROR
            return _with(result, phase, terminated.get("reason"), terminated.get("message"))

    if status.get("phase") == "Failed":
        return _with(result, SessionPhase.ERROR, status.get("reason"), status.get("message"))
    if meta.get("deletionTimestamp"):
        return _with(result, SessionPhase.TERMINATING, None, None)
    if not result.node_name:
        return _with(result, SessionPhase.PENDING, None, None)
    if _condition(pod, "Initialized") != "True":
        return _with(result, SessionPhase.PREPARING, None, None)
    if main is None or "running" not in main.get("state", {}):
        return _with(result, SessionPhase.PULLING, None, None)
    if _condition(pod, "Ready") == "True":
        return _with(result, SessionPhase.RUNNING, None, None)
    return _with(result, SessionPhase.CREATING, None, None)


def _with(
    result: KernelStatus, phase: SessionPhase, reason: str | None, message: str | None
) -> KernelStatus:
    result.phase = phase
    result.reason = reason
    result.message = message
    return result


def session_phase(kernels: Sequence[KernelStatus], deleting: bool) -> SessionPhase:
    phases = [SessionPhase(k.phase) for k in kernels]
    if deleting:
        return SessionPhase.TERMINATING
    if any(p == SessionPhase.ERROR for p in phases):
        return SessionPhase.ERROR
    # One kernel leaving ends the session: the Agent path does the same.
    if any(p in (SessionPhase.TERMINATED, SessionPhase.TERMINATING) for p in phases):
        return SessionPhase.TERMINATED
    return min(phases, key=_ORDER.index, default=SessionPhase.PENDING)
