from collections.abc import Mapping, Sequence
from typing import Any, cast, override

from ai.backend.agent.containerd.orchestrator import ContainerdKernelOrchestrator
from ai.backend.agent.containerd.runtime import ContainerdRuntimeClient, TaskHandle
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


class FakeRuntime(ContainerdRuntimeClient):
    """Records the runtime call order; returns a fixed task PID."""

    def __init__(self, pid: int = 4242) -> None:
        self.calls: list[str] = []
        self._pid = pid

    @override
    async def image_exists(self, image_ref: str) -> bool:
        return True

    @override
    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        self.calls.append("pull_image")

    @override
    async def list_images(self) -> Sequence[str]:
        return []

    @override
    async def remove_image(self, image_ref: str) -> None:
        self.calls.append("remove_image")

    @override
    async def push_image(self, image_ref: str) -> None:
        self.calls.append("push_image")

    @override
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        return ["/entry"]

    @override
    async def container_status(self, container_id: str) -> str | None:
        return "running"

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
    async def start_container(self, container_id: str) -> TaskHandle:
        self.calls.append("start_container")
        return TaskHandle(container_id=container_id, pid=self._pid)

    @override
    async def kill_container(self, container_id: str, *, signal: int) -> None:
        self.calls.append("kill_container")

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
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def __call__(
        self, command: str, *, ifname: str, netns: str, container_id: str, config: Any
    ) -> None:
        self.calls.append((command, netns))


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


class TestLaunch:
    async def test_order_create_task_then_attach_then_start(self) -> None:
        runtime = FakeRuntime(pid=4242)
        runner = RecordingNetworkRunner()
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
        # runtime creates + starts the container BEFORE the network attaches
        assert runtime.calls == ["create_container", "start_container"]
        # network attach happened against the task's PID netns
        assert runner.calls == [("ADD", "/proc/4242/ns/net")]
        assert result.handle.pid == 4242

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
        assert runtime.calls == ["create_container", "start_container"]
        assert runner.calls == [("ADD", "/proc/4242/ns/net")]
        assert result.handle.pid == 4242
