"""Unit tests for ContainerdKernelCreationContext network lifecycle.

The heavy AbstractKernelCreationContext.__init__ is bypassed via __new__ + manual field
injection so the lifecycle methods can be tested in isolation against a fake facade.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast, override

import pytest

from ai.backend.agent.config.unified import ScratchType
from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext
from ai.backend.agent.containerd.oci import AcceleratorSpec
from ai.backend.agent.containerd.orchestrator import LaunchResult
from ai.backend.agent.containerd.runtime.interface import TaskHandle
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.resources import Mount
from ai.backend.common.network.types import (
    AttachKind,
    EndpointPlan,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)
from ai.backend.common.types import MountPermission, MountTypes

_VXLAN_NC = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4097, "mtu": 1450}


class FakeFacade:
    def __init__(self) -> None:
        self.ensured: list[tuple[str, dict[str, Any]]] = []
        self.started: list[tuple[str, str]] = []

    async def create_container(
        self, session_id: str, container_id: str, *, image_ref: str, command: Any, oci_spec: Any
    ) -> None:
        pass

    async def ensure_session(self, session_id: str, network_config: Any) -> SessionNetMeta:
        self.ensured.append((session_id, dict(network_config)))
        return SessionNetMeta(
            session_id=session_id,
            subnet=network_config["subnet"],
            backend=NetworkBackendKind(network_config["backend"]),
            mtu=int(network_config.get("mtu") or 1500),
            vni=network_config.get("vni"),
        )

    async def start_and_attach_container(
        self,
        session_id: str,
        container_id: str,
        *,
        meta: Any,
        kernel_config: Any,
        cluster_info: Any,
    ) -> LaunchResult:
        self.started.append((session_id, container_id))
        plan = EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="baimulti0",
                    role=NetworkRole.OVERLAY,
                    ip="10.128.5.7",
                    cni_config={},
                )
            ]
        )
        return LaunchResult(
            handle=TaskHandle(container_id=container_id, pid=555),
            plan=plan,
            # agent reaches the kernel via the LOCAL interface (host is its gateway),
            # NOT the overlay IP (unreachable from the host)
            endpoint_ips={NetworkRole.LOCAL: "172.30.1.2", NetworkRole.OVERLAY: "10.128.5.7"},
        )


_ADVERTISED_HOST = "10.0.0.1"


class FakePortForwarder:
    """Records the DNAT rules the context asks for."""

    def __init__(self) -> None:
        self.installed: list[Any] = []

    async def install(self, forwards: Any) -> None:
        self.installed.extend(forwards)


def _context(
    facade: FakeFacade, *, port_forwarder: FakePortForwarder | None = None
) -> ContainerdKernelCreationContext:
    ctx = ContainerdKernelCreationContext.__new__(ContainerdKernelCreationContext)
    ctx._session_network = cast(Any, facade)
    ctx._session_id = "sess-abc"
    ctx._container_id = "kern-123"
    ctx._net_meta = None
    ctx._oci_mounts = []
    ctx._scratch_dir = None
    ctx._accel_spec = AcceleratorSpec()
    ctx._pending_spec = SimpleNamespace(
        image_ref="img:1", oci_spec={}, command=["/opt/kernel/entrypoint.sh"]
    )
    ctx.kernel_config = cast(Any, {})
    ctx._port_forwarder = cast(Any, port_forwarder)
    # what _reserve_host_ports would have produced: one service port, no REPL port
    ctx._host_port_map = [(30003, 8070)]
    ctx._port_pool = PortPool((30000, 30010), 0.0)
    ctx._port_pool.discard(30003)  # _reserve_host_ports had acquired it
    ctx.local_config = cast(
        Any,
        SimpleNamespace(
            container=SimpleNamespace(advertised_host=_ADVERTISED_HOST, bind_host="0.0.0.0")
        ),
    )
    return ctx


class _FakeComputer:
    """Compute plugin stub whose generate_docker_args returns a fixed Docker HostConfig."""

    def __init__(self, docker_args: dict[str, Any]) -> None:
        self._docker_args = docker_args

    async def generate_docker_args(self, docker: Any, device_alloc: Any) -> dict[str, Any]:
        return self._docker_args


class TestApplyNetwork:
    async def test_sets_up_session_when_backend_present(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        assert facade.ensured == [("sess-abc", _VXLAN_NC)]
        assert ctx._net_meta is not None
        assert ctx._net_meta.vni == 4097

    async def test_synthesizes_bridge_without_backend(self) -> None:
        # single-node: no manager backend -> synthesize a node-local BRIDGE config so the
        # same CNI path applies (no nerdctl-managed network).
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(cast(Any, {"network_config": {}}))
        assert len(facade.ensured) == 1
        assert facade.ensured[0][1]["backend"] == "bridge"
        assert ctx._net_meta is not None
        assert ctx._net_meta.backend is NetworkBackendKind.BRIDGE

    async def test_synthesizes_bridge_without_network_config(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(cast(Any, {}))
        assert len(facade.ensured) == 1
        assert facade.ensured[0][1]["backend"] == "bridge"


class TestScratchAndMounts:
    async def test_prepare_scratch_creates_config_and_work(self, tmp_path: Path) -> None:
        ctx = _context(FakeFacade())
        ctx.local_config = cast(
            Any,
            SimpleNamespace(
                container=SimpleNamespace(scratch_root=tmp_path, scratch_type=ScratchType.HOSTDIR)
            ),
        )
        await ctx.prepare_scratch()
        assert (tmp_path / "kern-123" / "config").is_dir()
        assert (tmp_path / "kern-123" / "work").is_dir()
        assert ctx._scratch_dir == (tmp_path / "kern-123").resolve()

    async def test_prepare_scratch_hostfile_creates_loop_fs(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        # HOSTFILE backs the scratch with a loop-mounted image; prepare_scratch must invoke
        # create_loop_filesystem (with the kernel id + configured size) before making config/work.
        calls: list[tuple[Any, ...]] = []

        async def fake_create(root: Any, size: int, kid: Any) -> None:
            calls.append((root, size, kid))

        monkeypatch.setattr("ai.backend.agent.containerd.agent.create_loop_filesystem", fake_create)
        monkeypatch.setattr("ai.backend.agent.containerd.agent.sys.platform", "linux")
        ctx = _context(FakeFacade())
        ctx.kernel_id = cast(Any, "kern-123")
        ctx.local_config = cast(
            Any,
            SimpleNamespace(
                container=SimpleNamespace(
                    scratch_root=tmp_path,
                    scratch_type=ScratchType.HOSTFILE,
                    scratch_size=1024,
                )
            ),
        )
        await ctx.prepare_scratch()
        assert calls == [(tmp_path, 1024, "kern-123")]
        assert (tmp_path / "kern-123" / "config").is_dir()

    async def test_process_mounts_accumulates(self) -> None:
        ctx = _context(FakeFacade())
        m = Mount(MountTypes.BIND, Path("/host/x"), Path("/opt/x"), MountPermission.READ_ONLY)
        await ctx.process_mounts([m])
        assert ctx._oci_mounts == [m]

    def test_get_runner_mount_builds_mount(self) -> None:
        ctx = _context(FakeFacade())
        m = ctx.get_runner_mount(MountTypes.BIND, "/host/su-exec", "/opt/kernel/su-exec")
        assert m.type is MountTypes.BIND
        assert str(m.target) == "/opt/kernel/su-exec"
        assert m.permission is MountPermission.READ_ONLY

    def test_resolve_krunner_filepath_ends_with_name(self) -> None:
        ctx = _context(FakeFacade())
        p = ctx.resolve_krunner_filepath("runner/su-exec.x86_64.bin")
        assert p.name == "su-exec.x86_64.bin"


class TestStartContainer:
    async def test_single_node_bridge_uses_cni_path_and_publishes_ports(self) -> None:
        # single-node: apply_network synthesizes a bridge meta, then start goes through the
        # SAME create_container + start_and_attach CNI path.
        facade = FakeFacade()
        ctx = _context(facade, port_forwarder=FakePortForwarder())
        await ctx.apply_network(cast(Any, {}))
        result = await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert facade.started == [("sess-abc", "kern-123")]
        assert result["kernel_host"] == _ADVERTISED_HOST
        assert result["task_pid"] == 555

    async def test_kernel_host_is_the_agent_advertised_address(self) -> None:
        # NOT the LOCAL IP: that is a node-local NAT address, and the manager hands kernel_host to
        # an AppProxy that may run on any host. NOT the overlay IP either: that is reachable only
        # between kernels.
        facade = FakeFacade()
        ctx = _context(facade, port_forwarder=FakePortForwarder())
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        result = await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert facade.started == [("sess-abc", "kern-123")]
        assert result["kernel_host"] == _ADVERTISED_HOST
        assert result["kernel_host"] != "172.30.1.2"
        assert result["task_pid"] == 555
        assert result["container_id"] == "kern-123"

    async def test_the_repl_is_dialled_directly_not_published(self) -> None:
        # the agent is on this node, so the REPL needs no host port and no DNAT; publishing it
        # would also make the agent's own dial depend on route_localnet when it advertises 127.0.0.1
        ctx = _context(FakeFacade(), port_forwarder=FakePortForwarder())
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        result = await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert result["repl_host"] == "172.30.1.2"  # the container's own LOCAL address
        assert (result["repl_in_port"], result["repl_out_port"]) == ctx.repl_ports  # 2000/2001
        assert result["host_ports"] == [30003]  # only the service port

    async def test_only_service_ports_are_dnatd_to_the_container(self) -> None:
        forwarder = FakePortForwarder()
        ctx = _context(FakeFacade(), port_forwarder=forwarder)
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert [(f.host_port, f.container_port) for f in forwarder.installed] == [(30003, 8070)]
        assert {f.container_ip for f in forwarder.installed} == {"172.30.1.2"}

    async def test_a_missing_publisher_fails_loudly(self) -> None:
        # publishing silently is the one outcome we cannot allow: the kernel would come up with
        # every service unreachable, and nothing would say so.
        ctx = _context(FakeFacade(), port_forwarder=None)
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        with pytest.raises(RuntimeError):
            await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))

    async def test_a_start_failure_releases_the_reserved_host_ports(self) -> None:
        # _reserve_host_ports (in prepare) took the port from the pool; if start fails it was never
        # published, so nothing in iptables reclaims it — start_container must release it here or it
        # leaks from the pool until the agent restarts.
        class _FailingFacade(FakeFacade):
            @override
            async def start_and_attach_container(self, *a: Any, **k: Any) -> Any:
                raise RuntimeError("container failed to start")

        ctx = _context(_FailingFacade(), port_forwarder=FakePortForwarder())
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        before = len(ctx._port_pool)
        with pytest.raises(RuntimeError):
            await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert len(ctx._port_pool) == before + 1  # 30003 returned to the pool

    async def test_a_successful_start_does_not_release_the_pool(self) -> None:
        # the published launch releases via clean_kernel later; releasing here too would double-free
        ctx = _context(FakeFacade(), port_forwarder=FakePortForwarder())
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        before = len(ctx._port_pool)
        await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert len(ctx._port_pool) == before  # unchanged: still held


class TestAcceleratorAllocation:
    async def test_nvidia_and_device_accumulate(self) -> None:
        ctx = _context(FakeFacade())
        nvidia = _FakeComputer({
            "HostConfig": {"DeviceRequests": [{"Driver": "nvidia", "DeviceIDs": ["0"]}]}
        })
        npu = _FakeComputer({"HostConfig": {"Devices": [{"PathOnHost": "/dev/rbln0"}]}})
        await ctx.apply_accelerator_allocation(cast(Any, nvidia), cast(Any, {}))
        await ctx.apply_accelerator_allocation(cast(Any, npu), cast(Any, {}))
        # accumulated across accelerators
        assert ctx._accel_spec.gpu_device_ids == ["0"]
        assert [d.source for d in ctx._accel_spec.devices] == ["/dev/rbln0"]
