"""Turn kernel phase changes into the kernel events the Manager takes from an Agent.

The last phase sent is kept in the SessionWorkload status (`reportedPhase`), so a restart
resends nothing and misses nothing. Events go in order, skipped phases included, because
the Manager moves a kernel only SCHEDULED → PULLING → CREATING → RUNNING.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Final
from uuid import UUID

from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.kernel.anycast import (
    KernelCreatingAnycastEvent,
    KernelPullingAnycastEvent,
    KernelStartedAnycastEvent,
    KernelTerminatedAnycastEvent,
)
from ai.backend.common.events.event_types.kernel.broadcast import (
    KernelStartedBroadcastEvent,
    KernelTerminatedBroadcastEvent,
)
from ai.backend.common.events.event_types.kernel.types import (
    KernelCreationInfo,
    KernelLifecycleEventReason,
    ServicePortInfo,
    UsedDevice,
    UsedDevices,
)
from ai.backend.common.types import (
    ContainerId,
    DeviceId,
    DeviceName,
    KernelId,
    ServicePortProtocols,
    SessionId,
)
from ai.backend.kube.controller.logs import KernelLogSync
from ai.backend.kube.controller.manifests import REPL_PORTS, kernel_service_ports
from ai.backend.kube.controller.naming import LABEL_KERNEL_ID
from ai.backend.kube.controller.status import kernel_status_from_pod
from ai.backend.kube.crd.session import KernelSpec, KernelStatus, SessionPhase, SessionWorkload

ANNOTATION_TERMINATION_REASON: Final = "backend.ai/termination-reason"
_ENDED: Final = frozenset({SessionPhase.TERMINATED, SessionPhase.ERROR})
_RANK: Final = {
    SessionPhase.PENDING: 0,
    SessionPhase.SCHEDULED: 1,
    SessionPhase.PREPARING: 2,
    SessionPhase.PULLING: 3,
    SessionPhase.CREATING: 4,
    SessionPhase.RUNNING: 5,
    SessionPhase.TERMINATING: 5,
    SessionPhase.TERMINATED: 6,
    SessionPhase.ERROR: 6,
}
_POD_DEVICE: Final = DeviceId("pod")


def _creation_info(kernel: KernelSpec, status: KernelStatus) -> KernelCreationInfo:
    ports = [
        ServicePortInfo(
            name=p.name,
            protocol=ServicePortProtocols(p.protocol),
            container_ports=p.container_ports,
            # Pod IPs are reachable directly, so a service listens on its own port.
            host_ports=list(p.container_ports),
            is_inference=p.is_inference,
        )
        for p in kernel_service_ports(kernel)
    ]
    units = {
        DeviceName(slot): {
            _POD_DEVICE: UsedDevice(
                model_name=None,
                used={ResourceSlotName(slot): Decimal(value)},
                processing_units=None,
                memory_size=None,
            )
        }
        for slot, value in kernel.resource_slots.items()
        if Decimal(value) != 0
    }
    return KernelCreationInfo(
        container_id=ContainerId(status.container_id or status.pod_uid or ""),
        kernel_host=status.pod_ip or "",
        repl_in_port=REPL_PORTS[0],
        repl_out_port=REPL_PORTS[1],
        service_ports=ports,
        used_devices=UsedDevices(units=units),
    )


def _termination_reason(
    workload: SessionWorkload, status: KernelStatus, reached_running: bool
) -> KernelLifecycleEventReason:
    requested = (workload.metadata.get("annotations") or {}).get(ANNOTATION_TERMINATION_REASON)
    if requested is not None and (reason := KernelLifecycleEventReason.from_value(requested)):
        return reason
    if status.phase == SessionPhase.ERROR:
        return (
            KernelLifecycleEventReason.ABNORMAL_TERMINATION
            if reached_running
            else KernelLifecycleEventReason.FAILED_TO_START
        )
    return KernelLifecycleEventReason.SELF_TERMINATED


class StatusReporter:
    _producer: EventProducer
    _logs: KernelLogSync | None

    def __init__(self, producer: EventProducer, logs: KernelLogSync | None = None) -> None:
        self._producer = producer
        self._logs = logs

    async def hand_over_logs(
        self, workload: SessionWorkload, pods: Sequence[Mapping[str, Any]]
    ) -> None:
        """Before the controller deletes the Pods of a session: they take their logs along."""
        if self._logs is None:
            return
        for pod in pods:
            if pod["metadata"].get("deletionTimestamp"):
                continue
            status = kernel_status_from_pod(pod["metadata"]["labels"][LABEL_KERNEL_ID], pod)
            if status.pod_name and status.container_id:
                await self._logs.sync(
                    workload.metadata["namespace"],
                    status.pod_name,
                    KernelId(UUID(status.kernel_id)),
                    status.container_id,
                )

    async def report(
        self, workload: SessionWorkload, statuses: Sequence[KernelStatus]
    ) -> list[KernelStatus]:
        """Send what changed since the last report; return the statuses with it recorded.

        A failed send raises, leaving `reportedPhase` where it was for the next reconcile.
        """
        specs = {k.kernel_id: k for k in workload.spec.kernels}
        reported: list[KernelStatus] = []
        for status in statuses:
            spec = specs.get(status.kernel_id)
            if spec is not None:
                status = await self._report_kernel(workload, spec, status)
            reported.append(status)
        return reported

    async def _report_kernel(
        self, workload: SessionWorkload, spec: KernelSpec, status: KernelStatus
    ) -> KernelStatus:
        last = SessionPhase(status.reported_phase) if status.reported_phase else None
        if last in _ENDED:
            return status
        last_rank = _RANK[last] if last is not None else 0
        phase = SessionPhase(status.phase)
        kernel_id = KernelId(UUID(spec.kernel_id))
        session_id = SessionId(UUID(workload.spec.session_id))
        reason = KernelLifecycleEventReason.TRIGGERED_BY_SCHEDULER
        sent = last
        if phase not in _ENDED and _RANK[phase] >= _RANK[SessionPhase.PREPARING]:
            if last_rank < _RANK[SessionPhase.PULLING]:
                await self._producer.anycast_event(
                    KernelPullingAnycastEvent(
                        kernel_id=kernel_id, session_id=session_id, reason=spec.image.canonical
                    )
                )
                sent = SessionPhase.PULLING
            if (
                _RANK[phase] >= _RANK[SessionPhase.CREATING]
                and last_rank < _RANK[SessionPhase.CREATING]
            ):
                await self._producer.anycast_event(
                    KernelCreatingAnycastEvent(
                        kernel_id=kernel_id, session_id=session_id, reason=reason
                    )
                )
                sent = SessionPhase.CREATING
            if phase == SessionPhase.RUNNING and last_rank < _RANK[SessionPhase.RUNNING]:
                info = _creation_info(spec, status)
                await self._producer.anycast_and_broadcast_event(
                    KernelStartedAnycastEvent(
                        kernel_id=kernel_id,
                        session_id=session_id,
                        reason=reason,
                        creation_info=info,
                    ),
                    KernelStartedBroadcastEvent(
                        kernel_id=kernel_id,
                        session_id=session_id,
                        reason=reason,
                        creation_info=info,
                    ),
                )
                sent = SessionPhase.RUNNING
        elif phase in _ENDED:
            term_reason = _termination_reason(
                workload, status, last_rank >= _RANK[SessionPhase.RUNNING]
            )
            exit_code = status.exit_code if status.exit_code is not None else -1
            if self._logs is not None and status.pod_name and status.container_id:
                await self._logs.sync(
                    workload.metadata["namespace"], status.pod_name, kernel_id, status.container_id
                )
            await self._producer.anycast_and_broadcast_event(
                KernelTerminatedAnycastEvent(
                    kernel_id=kernel_id,
                    session_id=session_id,
                    reason=term_reason,
                    exit_code=exit_code,
                ),
                KernelTerminatedBroadcastEvent(
                    kernel_id=kernel_id,
                    session_id=session_id,
                    reason=term_reason,
                    exit_code=exit_code,
                ),
            )
            sent = phase
        if sent == last:
            return status
        return status.model_copy(update={"reported_phase": sent})
