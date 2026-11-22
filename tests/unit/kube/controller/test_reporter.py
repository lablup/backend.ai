from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

import pytest

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.kernel.anycast import (
    KernelStartedAnycastEvent,
    KernelTerminatedAnycastEvent,
)
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.events.types import AbstractAnycastEvent, AbstractBroadcastEvent
from ai.backend.common.types import AgentId, KernelId
from ai.backend.kube.controller.logs import KernelLogSync
from ai.backend.kube.controller.reporter import ANNOTATION_TERMINATION_REASON, StatusReporter
from ai.backend.kube.crd.session import KernelStatus, SessionPhase, SessionWorkload

KERNEL_ID = "11111111-0000-0000-0000-000000000001"


class RecordingProducer(EventProducer):
    """Keeps the anycast events instead of sending them."""

    sent: list[AbstractAnycastEvent]

    def __init__(self) -> None:
        self.sent = []

    @override
    async def anycast_event(
        self, event: AbstractAnycastEvent, source_override: AgentId | None = None
    ) -> None:
        self.sent.append(event)

    @override
    async def anycast_and_broadcast_event(
        self,
        anycast_event: AbstractAnycastEvent,
        broadcast_event: AbstractBroadcastEvent,
        source_override: AgentId | None = None,
    ) -> None:
        self.sent.append(anycast_event)


@pytest.fixture
def producer() -> RecordingProducer:
    return RecordingProducer()


@pytest.fixture
def reporter(producer: RecordingProducer) -> StatusReporter:
    return StatusReporter(producer)


def _status(phase: SessionPhase, reported: SessionPhase | None = None) -> KernelStatus:
    return KernelStatus(
        kernel_id=KERNEL_ID,
        phase=phase,
        reported_phase=reported,
        pod_uid="pod-uid",
        pod_ip="10.0.0.7",
        container_id="cid",
        exit_code=0 if phase == SessionPhase.TERMINATED else None,
    )


def _names(events: Sequence[AbstractAnycastEvent]) -> list[str]:
    return [e.event_name() for e in events]


class TestStatusReporter:
    async def test_running_sends_every_skipped_step_in_order(
        self, reporter: StatusReporter, producer: RecordingProducer, workload: SessionWorkload
    ) -> None:
        [status] = await reporter.report(workload, [_status(SessionPhase.RUNNING)])
        assert _names(producer.sent) == ["kernel_pulling", "kernel_creating", "kernel_started"]
        assert status.reported_phase == SessionPhase.RUNNING

    async def test_started_event_carries_the_pod_address(
        self, reporter: StatusReporter, producer: RecordingProducer, workload: SessionWorkload
    ) -> None:
        await reporter.report(workload, [_status(SessionPhase.RUNNING)])
        started = producer.sent[-1]
        assert isinstance(started, KernelStartedAnycastEvent)
        info = started.creation_info
        assert (info.kernel_host, info.repl_in_port, info.container_id) == ("10.0.0.7", 2000, "cid")
        assert {p.name for p in info.service_ports} >= {"sshd", "ttyd"}

    async def test_reported_phase_is_not_sent_again(
        self, reporter: StatusReporter, producer: RecordingProducer, workload: SessionWorkload
    ) -> None:
        await reporter.report(workload, [_status(SessionPhase.RUNNING, SessionPhase.RUNNING)])
        assert producer.sent == []

    async def test_pending_sends_nothing(
        self, reporter: StatusReporter, producer: RecordingProducer, workload: SessionWorkload
    ) -> None:
        [status] = await reporter.report(workload, [_status(SessionPhase.PENDING)])
        assert producer.sent == [] and status.reported_phase is None

    async def test_failure_before_running_is_failed_to_start(
        self, reporter: StatusReporter, producer: RecordingProducer, workload: SessionWorkload
    ) -> None:
        await reporter.report(workload, [_status(SessionPhase.ERROR, SessionPhase.PULLING)])
        [terminated] = producer.sent
        assert isinstance(terminated, KernelTerminatedAnycastEvent)
        assert terminated.reason == KernelLifecycleEventReason.FAILED_TO_START

    async def test_requested_termination_reason_wins(
        self, reporter: StatusReporter, producer: RecordingProducer, workload: SessionWorkload
    ) -> None:
        workload.metadata["annotations"] = {ANNOTATION_TERMINATION_REASON: "idle-timeout"}
        await reporter.report(workload, [_status(SessionPhase.TERMINATED, SessionPhase.RUNNING)])
        [terminated] = producer.sent
        assert isinstance(terminated, KernelTerminatedAnycastEvent)
        assert terminated.reason == KernelLifecycleEventReason.IDLE_TIMEOUT

    async def test_ended_kernel_is_reported_once(
        self, reporter: StatusReporter, producer: RecordingProducer, workload: SessionWorkload
    ) -> None:
        await reporter.report(workload, [_status(SessionPhase.TERMINATED, SessionPhase.TERMINATED)])
        assert producer.sent == []


class RecordingLogs(KernelLogSync):
    """Records the kernels whose log would be handed over."""

    synced: list[tuple[str, str]]

    def __init__(self) -> None:
        self.synced = []

    @override
    async def sync(
        self, namespace: str, pod_name: str, kernel_id: KernelId, container_id: str
    ) -> None:
        self.synced.append((pod_name, container_id))


class TestKernelLogs:
    async def test_an_ended_kernel_hands_over_its_log_first(
        self, producer: RecordingProducer, workload: SessionWorkload
    ) -> None:
        logs = RecordingLogs()
        reporter = StatusReporter(producer, logs)
        status = _status(SessionPhase.TERMINATED, SessionPhase.RUNNING)
        status.pod_name = "s-1-main1"
        await reporter.report(workload, [status])
        assert logs.synced == [("s-1-main1", "cid")]
        assert _names(producer.sent) == ["kernel_terminated"]

    async def test_a_running_kernel_keeps_its_log(
        self, producer: RecordingProducer, workload: SessionWorkload
    ) -> None:
        logs = RecordingLogs()
        await StatusReporter(producer, logs).report(workload, [_status(SessionPhase.RUNNING)])
        assert logs.synced == []

    async def test_pods_about_to_be_deleted_hand_over_their_logs(
        self, producer: RecordingProducer, workload: SessionWorkload
    ) -> None:
        logs = RecordingLogs()

        def pod(name: str, deleting: bool) -> dict[str, Any]:
            meta: dict[str, Any] = {"name": name, "labels": {"backend.ai/kernel-id": KERNEL_ID}}
            if deleting:
                meta["deletionTimestamp"] = "2026-01-01T00:00:00Z"
            return {
                "metadata": meta,
                "spec": {"nodeName": "n1"},
                "status": {
                    "containerStatuses": [
                        {"name": "kernel", "containerID": f"containerd://{name}-cid", "state": {}}
                    ]
                },
            }

        await StatusReporter(producer, logs).hand_over_logs(
            workload, [pod("a", False), pod("b", True)]
        )
        assert logs.synced == [("a", "a-cid")]
