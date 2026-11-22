from __future__ import annotations

from typing import Any

import pytest

from ai.backend.kube.controller.status import kernel_status_from_pod, session_phase
from ai.backend.kube.crd.session import KernelStatus, SessionPhase


def _pod(
    *,
    node: str | None = "n1",
    initialized: bool = True,
    ready: bool = False,
    main_state: dict[str, Any] | None = None,
    init_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "conditions": [
            {"type": "Initialized", "status": "True" if initialized else "False"},
            {"type": "Ready", "status": "True" if ready else "False"},
        ],
        "podIP": "10.0.0.1",
    }
    if main_state is not None:
        status["containerStatuses"] = [
            {"name": "kernel", "state": main_state, "containerID": "containerd://abc"}
        ]
    if init_state is not None:
        status["initContainerStatuses"] = [{"name": "krunner", "state": init_state}]
    return {"metadata": {"name": "p", "uid": "u"}, "spec": {"nodeName": node}, "status": status}


class TestKernelStatusFromPod:
    @pytest.mark.parametrize(
        ("pod", "phase"),
        [
            (None, SessionPhase.PENDING),
            (_pod(node=None), SessionPhase.PENDING),
            (_pod(initialized=False, init_state={"running": {}}), SessionPhase.PREPARING),
            (_pod(main_state={"waiting": {"reason": "ContainerCreating"}}), SessionPhase.PULLING),
            (_pod(main_state={"running": {}}), SessionPhase.CREATING),
            (_pod(main_state={"running": {}}, ready=True), SessionPhase.RUNNING),
            (_pod(main_state={"terminated": {"exitCode": 0}}), SessionPhase.TERMINATED),
            (_pod(main_state={"terminated": {"exitCode": 137}}), SessionPhase.ERROR),
            (_pod(main_state={"waiting": {"reason": "ImagePullBackOff"}}), SessionPhase.ERROR),
            (
                _pod(initialized=False, init_state={"terminated": {"exitCode": 1}}),
                SessionPhase.ERROR,
            ),
        ],
        ids=[
            "no-pod",
            "unscheduled",
            "init-running",
            "creating-container",
            "not-ready",
            "ready",
            "exited",
            "killed",
            "pull-backoff",
            "init-failed",
        ],
    )
    def test_phase(self, pod: dict[str, Any] | None, phase: SessionPhase) -> None:
        assert kernel_status_from_pod("k", pod).phase == phase

    def test_records_container_id_without_runtime_prefix(self) -> None:
        status = kernel_status_from_pod("k", _pod(main_state={"running": {}}, ready=True))
        assert status.container_id == "abc"


class TestSessionPhase:
    def _kernels(self, *phases: SessionPhase) -> list[KernelStatus]:
        return [KernelStatus(kernel_id=str(i), phase=p) for i, p in enumerate(phases)]

    def test_slowest_kernel_wins(self) -> None:
        kernels = self._kernels(SessionPhase.RUNNING, SessionPhase.PULLING)
        assert session_phase(kernels, deleting=False) == SessionPhase.PULLING

    def test_any_error_fails_the_session(self) -> None:
        kernels = self._kernels(SessionPhase.RUNNING, SessionPhase.ERROR)
        assert session_phase(kernels, deleting=False) == SessionPhase.ERROR

    def test_one_exited_kernel_ends_the_session(self) -> None:
        kernels = self._kernels(SessionPhase.RUNNING, SessionPhase.TERMINATED)
        assert session_phase(kernels, deleting=False) == SessionPhase.TERMINATED

    def test_deletion_is_terminating(self) -> None:
        kernels = self._kernels(SessionPhase.RUNNING)
        assert session_phase(kernels, deleting=True) == SessionPhase.TERMINATING
