"""How a Docker kernel is attached by its CNI plugin: ADD while gated, release the gate, read the
result. Each failure leaks or hangs rather than erroring."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from ai.backend.agent.docker.agent import (
    DockerKernelCreationContext,
    container_from_docker_container,
)
from ai.backend.agent.docker.gate import stage_gate, wait_gated_pid
from ai.backend.agent.docker.locator import DockerContainerLocator
from ai.backend.agent.errors.agent import ContainerCreationError, ContainerStartupFailedError
from ai.backend.agent.errors.network import CniPluginNotInstalled
from ai.backend.agent.gate import READY_MARKER
from ai.backend.agent.network.cni import (
    CNI_ARG_KERNEL_ID,
    CNI_ARG_SESSION_ID,
    CniDns,
    CniIpConfig,
    CniPortMapping,
    CniRequest,
    CniResult,
)
from ai.backend.agent.network.locator import ContainerLocator
from ai.backend.common.docker import LabelName


class _FakeContainer:
    """A container that is running and parked, unless told otherwise."""

    def __init__(self, pid: int = 4242, running: bool = True) -> None:
        self.pid = pid
        self.running = running

    async def show(self) -> dict[str, Any]:
        return {
            "State": {
                "Running": self.running,
                "Pid": self.pid if self.running else 0,
                "Status": "running" if self.running else "exited",
                "ExitCode": 0 if self.running else 1,
            }
        }


class TestWaitingForTheGate:
    async def test_it_returns_the_parked_pid(self, tmp_path: Path) -> None:
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        (gate_dir / READY_MARKER).touch()
        assert await wait_gated_pid(_FakeContainer(pid=777), gate_dir) == 777

    async def test_a_container_that_died_first_is_reported_not_waited_on(
        self, tmp_path: Path
    ) -> None:
        # A broken image or a bad command; without this it would be waited on for the whole
        # timeout and then reported as slow rather than as broken.
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        with pytest.raises(ContainerStartupFailedError, match="exited before reaching the gate"):
            await wait_gated_pid(_FakeContainer(running=False), gate_dir)

    async def test_a_gate_that_never_opens_times_out(self, tmp_path: Path) -> None:
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        with pytest.raises(TimeoutError):
            await wait_gated_pid(_FakeContainer(), gate_dir, timeout_sec=0.3)

    async def test_a_parked_container_with_no_pid_is_refused(self, tmp_path: Path) -> None:
        # Docker reports 0 rather than null; attaching to PID 0 would target the host.
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        (gate_dir / READY_MARKER).touch()
        container = _FakeContainer(pid=0)
        with pytest.raises(ContainerStartupFailedError, match="no PID"):
            await wait_gated_pid(container, gate_dir)


class _RecordingPlugin:
    """A CNI plugin that answers every ADD with ``result``, or raises ``error``."""

    def __init__(self, result: CniResult | None = None, error: Exception | None = None) -> None:
        self.result = result or CniResult()
        self.error = error
        self.requests: list[CniRequest] = []

    async def add(self, request: CniRequest) -> CniResult:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def released(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """The gates released, instead of waiting on a wrapper no test container runs."""
    gates: list[Path] = []
    monkeypatch.setattr("ai.backend.agent.docker.agent.release_gate", gates.append)
    return gates


@pytest.fixture
def context(tmp_path: Path, released: list[Path]) -> Any:
    """Enough of a kernel creation context to drive the attach, parked at a gate that is ready."""
    ctx = object.__new__(DockerKernelCreationContext)
    ctx.config_dir = tmp_path
    ctx.kernel_id = cast(Any, "k1")
    ctx.kernel_config = cast(
        Any, {"session_id": "s1", "cluster_hostname": "main1", "cluster_network_ip": "10.1.0.7"}
    )
    ctx.local_config = cast(Any, SimpleNamespace(container=SimpleNamespace(dns=["9.9.9.9"])))
    ctx._cni_config = {"type": "vxlan", "subnet": "10.1.0.0/24"}
    ctx._cni_port_mappings = (CniPortMapping(host_port=30001, container_port=8080),)
    ctx._container_ip = None
    stage_gate(tmp_path / "gate")
    (tmp_path / "gate" / READY_MARKER).touch()
    return ctx


class TestChoosingTheNetwork:
    """A network config naming a plugin in ``type`` is that plugin's; one without is Docker's."""

    @staticmethod
    def _context(tmp_path: Path, plugin: Any) -> Any:
        ctx = object.__new__(DockerKernelCreationContext)
        ctx.config_dir = tmp_path
        ctx.kernel_config = cast(Any, {"session_id": "s1"})
        ctx.local_config = cast(Any, SimpleNamespace(container=SimpleNamespace(dns=["9.9.9.9"])))
        ctx._cni_plugin_ctx = cast(Any, SimpleNamespace(plugin_of=lambda config: plugin))
        ctx._cni_plugin = None
        ctx.container_configs = []
        return ctx

    async def test_a_named_plugin_gets_a_container_with_no_network(self, tmp_path: Path) -> None:
        plugin = _RecordingPlugin()
        ctx = self._context(tmp_path, plugin)
        await DockerKernelCreationContext.apply_network(
            ctx, cast(Any, {"network_config": {"type": "example"}})
        )
        assert ctx._cni_plugin is plugin
        (config,) = ctx.container_configs
        assert config["HostConfig"]["NetworkMode"] == "none"
        assert "nameserver 9.9.9.9" in (tmp_path / "resolv.conf").read_text()

    async def test_a_plugin_this_agent_has_not_loaded_fails_the_create(
        self, tmp_path: Path
    ) -> None:
        ctx = self._context(tmp_path, None)
        with pytest.raises(CniPluginNotInstalled):
            await DockerKernelCreationContext.apply_network(
                ctx, cast(Any, {"network_config": {"type": "example"}})
            )
        assert ctx.container_configs == []


class TestAttachingAtTheGate:
    async def test_the_add_names_the_container_its_netns_session_and_ports(
        self, context: Any
    ) -> None:
        plugin = _RecordingPlugin(CniResult(ips=[CniIpConfig("172.30.0.5/26")]))
        await DockerKernelCreationContext._attach_container_network(
            context, cast(Any, _FakeContainer(pid=777)), "cid-1", cast(Any, plugin)
        )
        (request,) = plugin.requests
        assert request.container_id == "cid-1"
        assert request.netns == "/proc/777/ns/net"
        assert request.args[CNI_ARG_SESSION_ID] == "s1"
        assert request.args[CNI_ARG_KERNEL_ID] == "k1"
        assert request.config == {"type": "vxlan", "subnet": "10.1.0.0/24"}
        assert request.runtime_config.port_mappings == (
            CniPortMapping(host_port=30001, container_port=8080),
        )
        assert request.runtime_config.ips == ("10.1.0.7",)

    async def test_the_primary_address_is_where_the_agent_dials(self, context: Any) -> None:
        plugin = _RecordingPlugin(CniResult(ips=[CniIpConfig("172.30.0.5/26")]))
        await DockerKernelCreationContext._attach_container_network(
            context, cast(Any, _FakeContainer()), "cid-1", cast(Any, plugin)
        )
        assert context._container_ip == "172.30.0.5"

    async def test_the_networks_nameservers_come_first(self, context: Any) -> None:
        plugin = _RecordingPlugin(
            CniResult(ips=[CniIpConfig("172.30.0.5/26")], dns=CniDns(nameservers=["172.30.0.1"]))
        )
        await DockerKernelCreationContext._attach_container_network(
            context, cast(Any, _FakeContainer()), "cid-1", cast(Any, plugin)
        )
        nameservers = [
            line.split()[1]
            for line in (context.config_dir / "resolv.conf").read_text().splitlines()
            if line.startswith("nameserver")
        ]
        assert nameservers == ["172.30.0.1", "9.9.9.9"]

    async def test_an_add_with_no_address_is_a_container_failure(self, context: Any) -> None:
        with pytest.raises(ContainerCreationError):
            await DockerKernelCreationContext._attach_container_network(
                context, cast(Any, _FakeContainer()), "cid-1", cast(Any, _RecordingPlugin())
            )

    async def test_the_gate_is_released_when_the_add_fails(
        self, context: Any, released: list[Path]
    ) -> None:
        # A container parked forever has no timeout and no message.
        plugin = _RecordingPlugin(error=RuntimeError("the privnet refused"))
        with pytest.raises(RuntimeError):
            await DockerKernelCreationContext._attach_container_network(
                context, cast(Any, _FakeContainer()), "cid-1", cast(Any, plugin)
            )
        assert released == [context.config_dir / "gate"]


class TestPortsDockerDoesNotReport:
    """A `none` container reports no ports; a restarted agent reads the reserved ones from a label,
    or it hands them out again."""

    @staticmethod
    def _container(ports: dict[str, Any], labels: dict[str, str]) -> Any:
        return cast(
            Any,
            _DockerShaped({
                "NetworkSettings": {"Ports": ports},
                "State": {"Status": "running"},
                "Config": {"Image": "img", "Labels": labels},
            }),
        )

    def test_the_label_stands_in_for_a_none_container(self) -> None:
        container = container_from_docker_container(
            self._container({}, {LabelName.PUBLISHED_PORTS: "2000:30000,8080:30001"})
        )
        assert [(p.private_port, p.host_port) for p in container.ports] == [
            (2000, 30000),
            (8080, 30001),
        ]

    def test_ports_docker_publishes_win(self) -> None:
        container = container_from_docker_container(
            self._container(
                {"8080/tcp": [{"HostIp": "0.0.0.0", "HostPort": "30005"}]},
                {LabelName.PUBLISHED_PORTS: "8080:30001"},
            )
        )
        assert [(p.private_port, p.host_port) for p in container.ports] == [(8080, 30005)]


class _DockerShaped(dict[str, Any]):
    id = "cid-1"


class TestTheLocator:
    def test_docker_brings_one(self) -> None:
        assert isinstance(DockerContainerLocator(), ContainerLocator)

    def test_it_declines_to_place_cgroups(self) -> None:
        # Docker places its own; only rootless backends ask a helper to create one.
        with pytest.raises(NotImplementedError):
            DockerContainerLocator().cgroup_path("c1")
