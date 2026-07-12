"""Unit tests for ContainerdKernelCreationContext network lifecycle.

The heavy AbstractKernelCreationContext.__init__ is bypassed via __new__ + manual field
injection so the lifecycle methods can be tested in isolation against a fake facade.
"""

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast, override

import pytest

from ai.backend.agent.config.unified import ScratchType
from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext
from ai.backend.agent.containerd.oci import AcceleratorSpec
from ai.backend.agent.containerd.orchestrator import LaunchResult
from ai.backend.agent.containerd.runtime.interface import ExecResult, TaskHandle
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.agent import ContainerCreationError
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
from ai.backend.common.types import MountPermission, MountTypes, ResourceGroupType

_VXLAN_NC = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4097, "mtu": 1450}


class FakeFacade:
    def __init__(self, exec_exit_code: int = 0) -> None:
        self.ensured: list[tuple[str, dict[str, Any]]] = []
        self.started: list[tuple[str, str]] = []
        self.execs: list[tuple[list[str], int | None]] = []
        self._exec_exit_code = exec_exit_code

    async def create_container(
        self, session_id: str, container_id: str, *, image_ref: str, command: Any, oci_spec: Any
    ) -> None:
        pass

    async def exec_in_container(
        self, container_id: str, args: Any, *, uid: int | None = None, **kwargs: Any
    ) -> ExecResult:
        self.execs.append((list(args), uid))
        return ExecResult(exit_code=self._exec_exit_code, stdout=b"", stderr=b"denied")

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
    facade: FakeFacade,
    *,
    port_forwarder: FakePortForwarder | None = None,
    internal_data: dict[str, Any] | None = None,
) -> ContainerdKernelCreationContext:
    ctx = ContainerdKernelCreationContext.__new__(ContainerdKernelCreationContext)
    ctx.internal_data = internal_data or {}
    ctx._session_network = cast(Any, facade)
    ctx._session_id = "sess-abc"
    ctx._container_id = "kern-123"
    ctx._net_meta = None
    ctx._oci_mounts = []
    ctx.domain_socket_proxies = []
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


class TestResolvConfMount:
    def _ctx_with_scratch(self, tmp_path: Path, dns: list[str]) -> Any:
        ctx = _context(FakeFacade())
        (tmp_path / "config").mkdir()
        ctx._scratch_dir = tmp_path
        ctx.local_config = cast(Any, SimpleNamespace(container=SimpleNamespace(dns=dns)))
        return ctx

    async def test_mounts_a_generated_resolv_conf(self, tmp_path: Path) -> None:
        # runc, unlike dockerd, synthesizes no resolver: without this bind mount the container
        # resolves no names at all.
        ctx = self._ctx_with_scratch(tmp_path, ["10.0.0.53"])
        mount = ctx._prepare_resolv_conf()
        assert mount is not None
        assert str(mount.target) == "/etc/resolv.conf"
        # search/options are inherited from whatever this machine's resolv.conf says, so assert on
        # the nameservers only — those are what the operator pinned.
        written = (tmp_path / "config" / "resolv.conf").read_text()
        assert [ln for ln in written.splitlines() if ln.startswith("nameserver")] == [
            "nameserver 10.0.0.53"
        ]

    async def test_is_unconditional_unlike_etc_hosts(self, tmp_path: Path) -> None:
        # /etc/hosts is only injected for cluster sessions; every container needs a resolver.
        ctx = self._ctx_with_scratch(tmp_path, ["10.0.0.53"])
        assert ctx._prepare_etc_hosts(cast(Any, {})) is None  # no cluster peers
        assert ctx._prepare_resolv_conf() is not None

    async def test_no_scratch_yields_no_mount(self) -> None:
        ctx = _context(FakeFacade())
        ctx._scratch_dir = None
        assert ctx._prepare_resolv_conf() is None


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

    async def test_sudo_session_provisions_sudoers_in_the_container(self) -> None:
        # /etc/sudoers.d lives in the image rootfs, not in any bind mount, so it can only be
        # written from inside the container — hence the exec, as root.
        facade = FakeFacade()
        ctx = _context(
            facade,
            port_forwarder=FakePortForwarder(),
            internal_data={"sudo_session_enabled": True},
        )
        await ctx.apply_network(cast(Any, {}))
        await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))

        assert len(facade.execs) == 1
        args, uid = facade.execs[0]
        assert "/etc/sudoers.d/01-bai-work" in args[-1]
        assert uid == 0

    async def test_no_sudo_session_execs_nothing(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade, port_forwarder=FakePortForwarder())
        await ctx.apply_network(cast(Any, {}))
        await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert facade.execs == []

    async def test_a_failed_sudoers_provision_fails_the_launch(self) -> None:
        # Silently starting a kernel whose sudo the user asked for and did not get is worse than
        # failing the launch.
        facade = FakeFacade(exec_exit_code=1)
        ctx = _context(
            facade,
            port_forwarder=FakePortForwarder(),
            internal_data={"sudo_session_enabled": True},
        )
        await ctx.apply_network(cast(Any, {}))
        with pytest.raises(ContainerCreationError):
            await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))

    async def test_block_service_ports_comes_from_internal_data(self) -> None:
        # It used to be hard-coded False, so ContainerdKernel.start_service (which reads this off
        # the kernel data) never enforced the manager's policy.
        facade = FakeFacade()
        ctx = _context(
            facade,
            port_forwarder=FakePortForwarder(),
            internal_data={"block_service_ports": True},
        )
        await ctx.apply_network(cast(Any, {}))
        result = await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert result["block_service_ports"] is True

    async def test_block_service_ports_defaults_to_false(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade, port_forwarder=FakePortForwarder())
        await ctx.apply_network(cast(Any, {}))
        result = await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert result["block_service_ports"] is False

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


class TestProtectedServices:
    def _ctx_with_rg(self, rg: Any) -> Any:
        ctx = _context(FakeFacade())
        ctx.local_config = cast(Any, SimpleNamespace(agent=SimpleNamespace(scaling_group_type=rg)))
        return ctx

    def test_ttyd_protected_on_a_storage_resource_group(self) -> None:
        # ttyd on a storage node is a shell into the storage host; it must not be exposed like an
        # ordinary service app. It used to be unprotected on every resource group.
        assert self._ctx_with_rg(ResourceGroupType.STORAGE).protected_services == ("ttyd",)

    def test_nothing_protected_on_compute(self) -> None:
        assert self._ctx_with_rg(ResourceGroupType.COMPUTE).protected_services == ()


class TestDomainSocketProxies:
    """Special service containers (the image importer) need a host socket, e.g. the docker socket.

    The host socket is never bind-mounted directly: each kernel gets a proxy socket that forwards
    to it. Containerd used to report `domain_socket_proxies: []` and mount nothing, so those
    sessions could not work at all.
    """

    def _ctx(self, tmp_path: Path, sockets: list[str]) -> Any:
        ctx = _context(FakeFacade(), internal_data={"domain_socket_proxies": sockets})
        ctx._scratch_dir = tmp_path
        ctx._agent_sock_path = None
        ctx.local_config = cast(
            Any,
            SimpleNamespace(
                agent=SimpleNamespace(ipc_base_path=tmp_path / "ipc"),
                container=SimpleNamespace(scratch_root=tmp_path, scratch_type=ScratchType.HOSTDIR),
                debug=SimpleNamespace(coredump=SimpleNamespace(enabled=False)),
            ),
        )
        return ctx

    async def test_no_proxies_requested_mounts_nothing(self, tmp_path: Path) -> None:
        ctx = self._ctx(tmp_path, [])
        mounts = await ctx.get_intrinsic_mounts()
        assert ctx.domain_socket_proxies == []
        assert not any("proxy" in str(m.source) for m in mounts)

    async def test_the_proxy_is_mounted_at_the_host_socket_path(self, tmp_path: Path) -> None:
        host_sock = tmp_path / "docker.sock"
        ctx = self._ctx(tmp_path, [str(host_sock)])
        mounts = await ctx.get_intrinsic_mounts()
        try:
            (proxy,) = ctx.domain_socket_proxies
            # the container sees the socket at its usual path...
            mount = next(m for m in mounts if str(m.target) == str(host_sock))
            # ...but what is mounted is OUR proxy socket, not the host's
            assert Path(str(mount.source)) == proxy.host_proxy_path
            assert proxy.host_proxy_path != host_sock
            assert proxy.host_proxy_path.exists()
        finally:
            for p in ctx.domain_socket_proxies:
                p.proxy_server.close()
                await p.proxy_server.wait_closed()

    async def test_the_proxy_forwards_to_the_host_socket(self, tmp_path: Path) -> None:
        host_sock = tmp_path / "upstream.sock"
        received: list[bytes] = []

        async def _handle(reader: Any, writer: Any) -> None:
            received.append(await reader.read(5))
            writer.write(b"pong")
            await writer.drain()
            writer.close()

        upstream = await asyncio.start_unix_server(_handle, str(host_sock))
        ctx = self._ctx(tmp_path, [str(host_sock)])
        await ctx.get_intrinsic_mounts()
        try:
            (proxy,) = ctx.domain_socket_proxies
            reader, writer = await asyncio.open_unix_connection(str(proxy.host_proxy_path))
            writer.write(b"hello")
            await writer.drain()
            assert await reader.read(4) == b"pong"
            writer.close()
            assert received == [b"hello"]
        finally:
            for p in ctx.domain_socket_proxies:
                p.proxy_server.close()
                await p.proxy_server.wait_closed()
            upstream.close()
            await upstream.wait_closed()


class TestRestartKeepsTheAllocation:
    async def test_restart_reads_back_resource_txt(self, tmp_path: Path) -> None:
        # A restart must keep the allocation the kernel already has. Re-deriving it from
        # resource_slots re-runs the allocator, which can hand out a different cpuset or a
        # different accelerator device than the one the kernel's processes are pinned to.
        config_dir = tmp_path / "kern-123" / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "resource.txt").write_text(
            "CID=kern-123\nSCRATCH_SIZE=0\nSLOTS={}\nMOUNTS=\n"
        )
        ctx = _context(FakeFacade())
        ctx.restarting = True
        ctx.local_config = cast(
            Any, SimpleNamespace(container=SimpleNamespace(scratch_root=tmp_path))
        )

        spec, resource_opts = await ctx.prepare_resource_spec()

        assert resource_opts is None  # the stored spec is authoritative on a restart
        assert spec is not None


class TestRefusesAV1NetworkDriver:
    """'overlay' (Docker Swarm) is the manager's DEFAULT inter-container driver, and the containerd
    backend cannot speak it. Quietly synthesizing a node-local bridge instead would bring the
    session up with kernels on separate per-node bridges, unable to reach each other, with nothing
    to say why. Refuse it instead.
    """

    async def test_overlay_is_refused(self) -> None:
        ctx = _context(FakeFacade())
        with pytest.raises(UnsupportedResource, match="overlay"):
            await ctx.apply_network(cast(Any, {"network_config": {"mode": "overlay"}}))

    async def test_the_refusal_names_the_fix(self) -> None:
        ctx = _context(FakeFacade())
        with pytest.raises(UnsupportedResource, match="cni"):
            await ctx.apply_network(cast(Any, {"network_config": {"mode": "overlay"}}))

    async def test_a_single_node_bridge_config_is_still_served(self) -> None:
        # The manager sends mode=bridge for single-node multi-kernel sessions; that one IS ours.
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(
            cast(Any, {"network_config": {"mode": "bridge", "network_name": "bai-singlenode-x"}})
        )
        assert facade.ensured[0][1]["backend"] == "bridge"

    async def test_no_network_config_at_all_is_still_served(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(cast(Any, {}))
        assert facade.ensured[0][1]["backend"] == "bridge"

    async def test_a_cni_config_is_served_as_given(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        assert facade.ensured[0][1]["backend"] == "vxlan"


class TestMemoryScratch:
    """MEMORY means the scratch lives in RAM, and it did not.

    The old behaviour gave the container a private tmpfs at /tmp and left /home/work on disk — so
    the scratch was not in memory at all, and /tmp was bounded by nothing but the kernel's default
    (half the host's RAM). Docker mounts a sized tmpfs over the scratch itself and binds a second
    one at /tmp; this now does the same.
    """

    def _ctx(self, tmp_path: Path, scratch_type: ScratchType) -> Any:
        ctx = _context(FakeFacade())
        ctx._scratch_dir = tmp_path / "kern-123"
        ctx._agent_sock_path = None
        ctx.local_config = cast(
            Any,
            SimpleNamespace(
                container=SimpleNamespace(scratch_root=tmp_path, scratch_type=scratch_type),
                debug=SimpleNamespace(coredump=SimpleNamespace(enabled=False)),
                agent=SimpleNamespace(ipc_base_path=tmp_path / "ipc"),
            ),
        )
        return ctx

    async def test_tmp_is_bound_from_the_host_tmpfs(self, tmp_path: Path) -> None:
        ctx = self._ctx(tmp_path, ScratchType.MEMORY)
        mounts = await ctx.get_intrinsic_mounts()

        tmp_mount = next(m for m in mounts if str(m.target) == "/tmp")
        # the host tmpfs prepare_scratch mounted — not a container-private one the agent cannot see
        assert Path(str(tmp_mount.source)) == tmp_path / "kern-123_tmp"

    async def test_other_scratch_types_get_no_tmp_mount(self, tmp_path: Path) -> None:
        ctx = self._ctx(tmp_path, ScratchType.HOSTDIR)
        mounts = await ctx.get_intrinsic_mounts()
        assert not any(str(m.target) == "/tmp" for m in mounts)


class TestCoredumpMount:
    def _ctx(self, tmp_path: Path, enabled: bool) -> Any:
        ctx = _context(FakeFacade())
        ctx._scratch_dir = tmp_path / "kern-123"
        ctx._agent_sock_path = None
        ctx.local_config = cast(
            Any,
            SimpleNamespace(
                container=SimpleNamespace(scratch_root=tmp_path, scratch_type=ScratchType.HOSTDIR),
                debug=SimpleNamespace(
                    coredump=SimpleNamespace(
                        enabled=enabled,
                        path=tmp_path / "coredumps",
                        core_path=Path("/var/crash"),
                    )
                ),
                agent=SimpleNamespace(ipc_base_path=tmp_path / "ipc"),
            ),
        )
        return ctx

    async def test_the_host_coredump_dir_is_bound_where_core_pattern_names_it(
        self, tmp_path: Path
    ) -> None:
        # The host's core_pattern writes cores to an absolute path; the container has to see that
        # path, or the kernel cannot write the core at all and the feature is silently inert.
        ctx = self._ctx(tmp_path, enabled=True)
        mounts = await ctx.get_intrinsic_mounts()

        core = next(m for m in mounts if str(m.target) == "/var/crash")
        assert Path(str(core.source)) == tmp_path / "coredumps"
        assert core.permission == MountPermission.READ_WRITE  # the kernel has to write into it

    async def test_disabled_mounts_nothing(self, tmp_path: Path) -> None:
        ctx = self._ctx(tmp_path, enabled=False)
        mounts = await ctx.get_intrinsic_mounts()
        assert not any(str(m.target) == "/var/crash" for m in mounts)
