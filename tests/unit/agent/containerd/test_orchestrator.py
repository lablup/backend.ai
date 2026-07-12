from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast, override

import pytest

from ai.backend.agent.containerd.orchestrator import ContainerdKernelOrchestrator
from ai.backend.agent.containerd.runtime.interface import ExecResult, OciRuntime, TaskHandle
from ai.backend.agent.network.provisioner import ContainerNetworkProvisioner
from ai.backend.common.network.types import (
    AttachKind,
    EndpointPlan,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)
from ai.backend.common.types import ClusterInfo, KernelCreationConfig

_META = SessionNetMeta(
    session_id="s1", subnet="10.128.5.0/24", backend=NetworkBackendKind.VXLAN, mtu=1450, vni=4097
)


def _plan() -> EndpointPlan:
    return EndpointPlan(
        attachments=[
            NetworkAttachSpec(
                kind=AttachKind.CNI,
                interface_name="baimulti0",
                role=NetworkRole.OVERLAY,
                cni_config={"type": "bridge"},
            )
        ]
    )


class FakeRuntime(OciRuntime):
    """Records the runtime call order; returns a fixed task PID."""

    def __init__(self, pid: int = 4242, events: list[str] | None = None) -> None:
        self.calls: list[str] = []
        self._pid = pid
        self._events = events  # optional shared ordering log (runtime + network interleaved)

    @override
    async def image_exists(self, image_ref: str) -> bool:
        return True

    @override
    async def image_digest(self, image_ref: str) -> str | None:
        return "sha256:x"

    @override
    async def image_config_digest(self, image_ref: str) -> str | None:
        return None

    @override
    async def export_image(self, image_ref: str, dest_path: Path) -> None:
        return None

    @override
    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        self.calls.append("pull_image")

    @override
    async def list_images(self) -> Sequence[str]:
        return []

    @override
    async def list_image_infos(self) -> Sequence[Any]:
        return []

    @override
    async def list_container_infos(self) -> Sequence[Any]:
        return []

    @override
    async def subscribe_task_events(self) -> Any:
        return
        yield  # pragma: no cover

    @override
    async def remove_image(self, image_ref: str, *, sync: bool = False) -> None:
        self.calls.append("remove_image")

    @override
    async def push_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        self.calls.append("push_image")

    @override
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        return ["/entry"]

    @override
    async def container_status(self, container_id: str) -> str | None:
        return "running"

    @override
    async def exec_in_container(
        self,
        container_id: str,
        args: Any,
        *,
        uid: int | None = None,
        gid: int | None = None,
        cwd: str | None = None,
        timeout_sec: float = 30.0,
    ) -> ExecResult:
        return ExecResult(exit_code=0, stdout=b"", stderr=b"")

    @override
    async def create_container(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: Sequence[str],
        oci_spec: Mapping[str, Any],
        network: str = "none",
    ) -> None:
        self.calls.append("create_container")

    @override
    async def create_task(self, container_id: str) -> TaskHandle:
        self.calls.append("create_task")
        if self._events is not None:
            self._events.append("create_task")
        return TaskHandle(container_id=container_id, pid=self._pid)

    @override
    async def start_task(self, container_id: str) -> None:
        self.calls.append("start_task")
        if self._events is not None:
            self._events.append("start_task")

    @override
    async def kill_container(
        self, container_id: str, *, signal: int, all_processes: bool = True
    ) -> None:
        self.calls.append("kill_container")

    @override
    async def stop_container(self, container_id: str, *, grace_period: float) -> None:
        self.calls.append("stop_container")

    @override
    async def commit_container(
        self, container_id: str, *, base_image_ref: str, target_ref: str, labels: Any = None
    ) -> None:
        self.calls.append("commit_container")

    @override
    async def remove_container(self, container_id: str) -> None:
        self.calls.append("remove_container")

    @override
    async def list_containers(self) -> Sequence[str]:
        return []

    @override
    async def container_pid(self, container_id: str) -> int | None:
        return self._pid


class RecordingNetworkRunner:
    def __init__(self, events: list[str] | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self._events = events

    async def __call__(
        self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
    ) -> None:
        self.calls.append((command, netns))
        if self._events is not None:
            self._events.append(f"attach:{command}")


def _orchestrator(
    runtime: FakeRuntime, runner: RecordingNetworkRunner
) -> ContainerdKernelOrchestrator:
    provisioner = ContainerNetworkProvisioner(cast(Any, _FixedPlanBackend()), runner)
    return ContainerdKernelOrchestrator(runtime, provisioner)


class _FixedPlanBackend:
    async def attach_endpoint(
        self, kernel_config: Any, cluster_info: Any, *, meta: SessionNetMeta
    ) -> EndpointPlan:
        return _plan()


class _StartFailRuntime(FakeRuntime):
    """FakeRuntime whose start_task fails, to exercise the post-attach cleanup path."""

    @override
    async def start_task(self, container_id: str) -> None:
        self.calls.append("start_task")
        raise RuntimeError("start failed")


class TestLaunch:
    async def test_order_create_task_then_attach_then_start(self) -> None:
        events: list[str] = []
        runtime = FakeRuntime(pid=4242, events=events)
        runner = RecordingNetworkRunner(events=events)
        orch = _orchestrator(runtime, runner)
        result = await orch.launch(
            "c1",
            image_ref="img",
            command=["sleep", "600"],
            oci_spec={},
            meta=_META,
            kernel_config=cast(KernelCreationConfig, {}),
            cluster_info=cast(ClusterInfo, {}),
        )
        # The task is created, THEN the network attaches, THEN the task starts (execs the user
        # command) — so the container process begins with its network already in place.
        assert events == ["create_task", "attach:ADD", "start_task"]
        assert runtime.calls == ["create_container", "create_task", "start_task"]
        # network attach happened against the task's PID netns
        assert runner.calls == [("ADD", "/proc/4242/ns/net")]
        assert result.handle.pid == 4242

    async def test_start_task_failure_detaches_the_attached_network(self) -> None:
        # attach succeeds, then start_task fails. The caller records the plan only on success, so
        # the orchestrator must detach here or the host veth / IPAM / MASQ would leak.
        runtime = _StartFailRuntime(pid=4242)
        runner = RecordingNetworkRunner()
        orch = _orchestrator(runtime, runner)
        with pytest.raises(RuntimeError):
            await orch.launch(
                "c1",
                image_ref="img",
                command=["sleep", "600"],
                oci_spec={},
                meta=_META,
                kernel_config=cast(KernelCreationConfig, {}),
                cluster_info=cast(ClusterInfo, {}),
            )
        assert ("ADD", "/proc/4242/ns/net") in runner.calls
        assert ("DEL", "/proc/4242/ns/net") in runner.calls  # attach undone on start failure

    async def test_terminate_detaches_before_runtime_teardown(self) -> None:
        runtime = FakeRuntime(pid=4242)
        runner = RecordingNetworkRunner()
        orch = _orchestrator(runtime, runner)
        await orch.terminate("c1", plan=_plan(), task_pid=4242)
        assert runner.calls == [("DEL", "/proc/4242/ns/net")]
        assert runtime.calls == ["kill_container", "remove_container"]


class TestSplitLifecycle:
    async def test_create_does_not_start_or_attach(self) -> None:
        runtime = FakeRuntime(pid=4242)
        runner = RecordingNetworkRunner()
        orch = _orchestrator(runtime, runner)
        await orch.create("c1", image_ref="img", command=["sleep", "1"], oci_spec={})
        assert runtime.calls == ["create_container"]  # no start
        assert runner.calls == []  # no attach

    async def test_start_and_attach_after_create(self) -> None:
        runtime = FakeRuntime(pid=4242)
        runner = RecordingNetworkRunner()
        orch = _orchestrator(runtime, runner)
        await orch.create("c1", image_ref="img", command=[], oci_spec={})
        result = await orch.start_and_attach(
            "c1",
            meta=_META,
            kernel_config=cast(KernelCreationConfig, {}),
            cluster_info=cast(ClusterInfo, {}),
        )
        assert runtime.calls == ["create_container", "create_task", "start_task"]
        assert runner.calls == [("ADD", "/proc/4242/ns/net")]
        assert result.handle.pid == 4242
