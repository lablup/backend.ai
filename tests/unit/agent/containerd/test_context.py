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
from ai.backend.agent.network.local_subnet import DEFAULT_LAYOUT
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.resources import Mount
from ai.backend.agent.types import MountInfo
from ai.backend.common.network.types import (
    AttachKind,
    EndpointPlan,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)
from ai.backend.common.types import (
    ClusterMode,
    MountPermission,
    MountTypes,
    ResourceGroupType,
)

_VXLAN_NC = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4097, "mtu": 1450}


class FakeFacade:
    def __init__(self, exec_exit_code: int = 0) -> None:
        self.ensured: list[tuple[str, dict[str, Any]]] = []
        self.reserved: list[tuple[str, str]] = []  # (session, kernel) claims made before creation
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

    async def ensure_session(
        self, session_id: str, kernel_id: str, network_config: Any
    ) -> SessionNetMeta:
        self.ensured.append((session_id, dict(network_config)))
        self.reserved.append((session_id, kernel_id))
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
    ctx.restarting = False
    ctx.kernel_features = frozenset({"uid-match"})
    ctx.uid = None
    ctx.main_gid = None
    ctx._port_forwarder = cast(Any, port_forwarder)
    # what _reserve_host_ports would have produced: one service port, no REPL port
    ctx._host_port_map = [(30003, 8070, None)]
    ctx._port_pool = PortPool((30000, 30010), 0.0)
    ctx._port_pool.discard(30003)  # _reserve_host_ports had acquired it
    ctx.local_config = cast(
        Any,
        SimpleNamespace(
            container=SimpleNamespace(
                advertised_host=_ADVERTISED_HOST,
                bind_host="0.0.0.0",
                local_subnet_layout=lambda: DEFAULT_LAYOUT,
            )
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
                container=SimpleNamespace(
                    scratch_root=tmp_path,
                    scratch_type=ScratchType.HOSTDIR,
                    deeplearning_samples_path=None,
                )
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

    async def test_missing_net_meta_still_releases_the_reserved_ports(self) -> None:
        # The net-meta guard used to raise BEFORE start_container's try, so its RuntimeError leaked
        # the ports _reserve_host_ports had already taken. It is inside the try now.
        ctx = _context(FakeFacade(), port_forwarder=FakePortForwarder())
        ctx._net_meta = None  # apply_network never ran
        before = len(ctx._port_pool)
        with pytest.raises(RuntimeError):
            await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert len(ctx._port_pool) == before + 1  # 30003 given back

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

    async def test_a_plugins_bind_mount_survives_the_merge(self) -> None:
        # the merge rebuilds the AcceleratorSpec from scratch; a field it forgets to carry (here,
        # mounts) is silently reset to [] and the accelerator loses its bind (n300's hugepages).
        ctx = _context(FakeFacade())
        n300 = _FakeComputer({
            "HostConfig": {
                "Mounts": [
                    {"Type": "bind", "Source": "/dev/hugepages-1G", "Target": "/dev/hugepages-1G"}
                ]
            }
        })
        await ctx.apply_accelerator_allocation(cast(Any, n300), cast(Any, {}))
        assert [str(m.source) for m in ctx._accel_spec.mounts] == ["/dev/hugepages-1G"]


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
                container=SimpleNamespace(
                    scratch_root=tmp_path,
                    scratch_type=ScratchType.HOSTDIR,
                    deeplearning_samples_path=None,
                ),
                debug=SimpleNamespace(coredump=SimpleNamespace(enabled=False)),
            ),
        )
        return ctx

    async def test_the_agent_socket_is_mounted_as_a_directory(self, tmp_path: Path) -> None:
        # A bind-mounted socket FILE pins the inode it had at mount time, and that inode dies with
        # the agent process — so every kernel that outlived an agent restart was left holding a
        # dangling socket, its hook and jail losing PID translation with no error anywhere. The
        # directory is mounted instead (the entrypoint links the well-known path to it), so the
        # socket a restarted agent re-creates is resolved at connect time.
        ctx = self._ctx(tmp_path, [])
        sock = tmp_path / "ipc" / "container" / "agent-i-test" / "agent.sock"
        ctx._agent_sock_path = sock

        mounts = await ctx.get_intrinsic_mounts()

        mount = next(m for m in mounts if str(m.target) == "/opt/kernel/agent-sock")
        assert Path(str(mount.source)) == sock.parent  # the directory, not the socket file
        assert not any(str(m.target) == "/opt/kernel/agent.sock" for m in mounts)

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
                container=SimpleNamespace(
                    scratch_root=tmp_path,
                    scratch_type=scratch_type,
                    deeplearning_samples_path=None,
                ),
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
                container=SimpleNamespace(
                    scratch_root=tmp_path,
                    scratch_type=ScratchType.HOSTDIR,
                    deeplearning_samples_path=None,
                ),
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


class TestTheKernelUserOwnsItsHome:
    """/home/work is the user's home, bind-mounted from the host scratch. The container's PID 1
    starts as root and drops to LOCAL_USER_ID before the user ever sees it (runner/entrypoint.sh),
    so anything a root agent writes there is root-owned — and the user cannot write to their own
    home: Jupyter cannot save, the shell cannot write history, the dotfiles are theirs in name only.

    The container cannot fix this for itself: a recursive chown inside would also take ownership of
    every vfolder mounted under /home/work. So the agent hands the files over on the host, exactly
    as the Docker backend does.
    """

    def _ctx(
        self,
        tmp_path: Path,
        monkeypatch: Any,
        *,
        root: bool = True,
        uid_match: bool = True,
        override: tuple[int | None, int | None] = (None, None),
    ) -> tuple[Any, list[tuple[Path, int, int]]]:
        chowned: list[tuple[Path, int, int]] = []

        monkeypatch.setattr(
            "ai.backend.agent.containerd.agent.os.geteuid", lambda: 0 if root else 1000
        )
        monkeypatch.setattr(
            "ai.backend.agent.containerd.agent.os.chown",
            lambda p, uid, gid: chowned.append((Path(p), uid, gid)),
        )
        ctx = _context(FakeFacade())
        ctx.kernel_features = frozenset({"uid-match"} if uid_match else set())
        ctx.uid, ctx.main_gid = override
        ctx.local_config = cast(
            Any,
            SimpleNamespace(
                container=SimpleNamespace(
                    scratch_root=tmp_path,
                    scratch_type=ScratchType.HOSTDIR,
                    kernel_uid=1000,
                    kernel_gid=1001,
                )
            ),
        )
        return ctx, chowned

    async def test_the_home_and_the_seeded_dotfiles_are_handed_over(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        ctx, chowned = self._ctx(tmp_path, monkeypatch)
        await ctx.prepare_scratch()

        work_dir = tmp_path / "kern-123" / "work"
        owned = {path for path, _uid, _gid in chowned}
        assert work_dir in owned  # the home itself: without it the user cannot create a file
        assert work_dir / ".bashrc" in owned
        assert work_dir / ".jupyter" in owned
        assert all(uid == 1000 and gid == 1001 for _p, uid, gid in chowned)

    async def test_every_file_we_seed_is_a_file_we_hand_over(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        # A seeded file missing from the chown list is a file the user cannot write. The two lists
        # are one list for exactly this reason.
        ctx, chowned = self._ctx(tmp_path, monkeypatch)
        await ctx.prepare_scratch()

        work_dir = tmp_path / "kern-123" / "work"
        seeded = {p for p in work_dir.rglob("*") if p.is_file()}
        owned = {path for path, _uid, _gid in chowned}
        assert seeded <= owned

    async def test_a_non_root_agent_chowns_nothing(self, tmp_path: Path, monkeypatch: Any) -> None:
        # It could not anyway; and it does not need to — the scratch is already its own, and the
        # kernel runs as the same uid.
        ctx, chowned = self._ctx(tmp_path, monkeypatch, root=False)
        await ctx.prepare_scratch()
        assert chowned == []

    async def test_without_uid_match_the_files_stay_as_they_are(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        ctx, chowned = self._ctx(tmp_path, monkeypatch, uid_match=False)
        await ctx.prepare_scratch()
        assert chowned == []

    async def test_an_overriding_uid_wins_over_uid_match(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        ctx, chowned = self._ctx(tmp_path, monkeypatch, override=(5000, 5001))
        await ctx.prepare_scratch()
        assert chowned
        assert all(uid == 5000 and gid == 5001 for _p, uid, gid in chowned)

    async def test_a_restart_does_not_overwrite_the_users_own_dotfiles(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        # A restart reuses the scratch. Re-seeding would replace the .bashrc the user edited with
        # ours — which is why the Docker backend seeds only on first creation.
        ctx, _chowned = self._ctx(tmp_path, monkeypatch)
        await ctx.prepare_scratch()
        bashrc = tmp_path / "kern-123" / "work" / ".bashrc"
        bashrc.write_text("# the user's own")

        restarted, _c = self._ctx(tmp_path, monkeypatch)
        restarted.restarting = True
        await restarted.prepare_scratch()

        assert bashrc.read_text() == "# the user's own"


class TestTheClusterKeyIsReadableByTheKernelUser:
    """id_cluster is written 0600 by a root agent, so the kernel's user cannot read it — and
    reading it is its entire purpose: passwordless chief<->worker SSH for MPI/torchrun/bssh."""

    async def _prepare(
        self, tmp_path: Path, monkeypatch: Any, *, root: bool = True
    ) -> list[tuple[Path, int, int]]:
        chowned: list[tuple[Path, int, int]] = []
        monkeypatch.setattr(
            "ai.backend.agent.containerd.agent.os.geteuid", lambda: 0 if root else 1000
        )
        monkeypatch.setattr(
            "ai.backend.agent.containerd.agent.os.chown",
            lambda p, uid, gid: chowned.append((Path(p), uid, gid)),
        )
        ctx = _context(FakeFacade())
        ctx._scratch_dir = tmp_path
        ctx.local_config = cast(
            Any,
            SimpleNamespace(container=SimpleNamespace(kernel_uid=1000, kernel_gid=1001)),
        )
        await ctx.prepare_ssh(
            cast(
                Any,
                {
                    "ssh_keypair": {"private_key": "PRIV", "public_key": "PUB"},
                    "cluster_ssh_port_mapping": None,
                },
            )
        )
        return chowned

    async def test_the_keypair_is_handed_to_the_kernel_user(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        chowned = await self._prepare(tmp_path, monkeypatch)
        owned = {path for path, _u, _g in chowned}
        ssh_dir = tmp_path / "config" / "ssh"
        assert ssh_dir / "id_cluster" in owned
        assert ssh_dir / "id_cluster.pub" in owned
        assert all(uid == 1000 and gid == 1001 for _p, uid, gid in chowned)

    async def test_the_private_key_stays_0600(self, tmp_path: Path, monkeypatch: Any) -> None:
        # Handing it over must not widen it: ssh refuses a group/world-readable private key.
        await self._prepare(tmp_path, monkeypatch)
        priv = tmp_path / "config" / "ssh" / "id_cluster"
        assert priv.stat().st_mode & 0o077 == 0

    async def test_a_non_root_agent_chowns_nothing(self, tmp_path: Path, monkeypatch: Any) -> None:
        assert await self._prepare(tmp_path, monkeypatch, root=False) == []


class _FakeComputePlugin:
    """An accelerator plugin of the shape the real ones have: handed a per-kernel directory, it
    writes what its device needs into it and mounts it (the IPU plugin writes an `ipuof` config
    there; the Hyperaccel LPU plugin mounts its runtime libraries)."""

    key = "ipu"

    def __init__(self) -> None:
        self.source_paths: list[Path] = []

    async def generate_mounts(self, source_path: Path, device_alloc: Any) -> list[MountInfo]:
        self.source_paths.append(source_path)
        (source_path / "ipuof.conf").write_text("device=0")
        return [
            MountInfo(MountTypes.BIND, source_path / "ipuof.conf", Path("/etc/ipuof.conf")),
            MountInfo(MountTypes.BIND, Path("/opt/hyperdex"), Path("/opt/hyperdex")),
        ]


class TestAcceleratorMounts:
    """Not every accelerator is served by device nodes and env vars alone. This used to return
    nothing at all, so those mounts were dropped silently: the kernel starts, and the device it was
    allocated is unusable from inside it."""

    def _ctx(self, tmp_path: Path) -> Any:
        ctx = _context(FakeFacade())
        ctx._scratch_dir = tmp_path
        return ctx

    async def test_the_plugin_gets_a_per_kernel_directory_to_write_into(
        self, tmp_path: Path
    ) -> None:
        ctx = self._ctx(tmp_path)
        computer = _FakeComputePlugin()

        await ctx.generate_accelerator_mounts(cast(Any, computer), cast(Any, {}))

        assert computer.source_paths == [tmp_path / "config" / "ipu"]
        assert (tmp_path / "config" / "ipu").is_dir()  # it must exist before the plugin writes

    async def test_the_plugins_mounts_are_returned(self, tmp_path: Path) -> None:
        ctx = self._ctx(tmp_path)
        mounts = await ctx.generate_accelerator_mounts(
            cast(Any, _FakeComputePlugin()), cast(Any, {})
        )

        targets = {str(m.dst_path) for m in mounts}
        assert targets == {"/etc/ipuof.conf", "/opt/hyperdex"}

    async def test_no_scratch_yields_no_mounts(self, tmp_path: Path) -> None:
        ctx = self._ctx(tmp_path)
        ctx._scratch_dir = None
        assert (
            await ctx.generate_accelerator_mounts(cast(Any, _FakeComputePlugin()), cast(Any, {}))
            == []
        )


class TestTheContainerIdReachesTheContainer:
    """`CID=` in resource.txt is the only place the in-container side learns its own container id.
    The jail / libbaihook abuse reporter puts it in the report the agent then acts on (the agent
    reads `body["CID"]`), so without it an abuse report names no container."""

    async def _write(self, tmp_path: Path) -> Path:
        # Driven through the real start_container, so the line cannot go missing by the call site
        # being dropped — which is exactly how it was missing in the first place.
        ctx = _context(FakeFacade(), port_forwarder=FakePortForwarder())
        ctx._scratch_dir = tmp_path
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "resource.txt").write_text("CPU_CORES=2\n")
        (tmp_path / "config" / "resource_base.txt").write_text("CPU_CORES=2\n")
        await ctx.apply_network(cast(Any, {}))
        await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        return tmp_path / "config"

    async def test_the_container_id_is_appended(self, tmp_path: Path) -> None:
        config_dir = await self._write(tmp_path)
        lines = (config_dir / "resource.txt").read_text().splitlines()
        assert "CID=kern-123" in lines
        assert "CPU_CORES=2" in lines  # what was already there survives

    async def test_the_base_copy_stays_pristine(self, tmp_path: Path) -> None:
        # resource_base.txt is the untouched copy the runner diffs against; the Docker backend
        # appends to resource.txt only, after the container exists.
        config_dir = await self._write(tmp_path)
        assert "CID=" not in (config_dir / "resource_base.txt").read_text()


class TestTheDeepLearningSamples:
    """The Docker backend mounts a named Docker volume at /home/work/samples for DL images.
    containerd has no volume registry, so the operator names the directory instead."""

    def _ctx(self, tmp_path: Path, *, samples: str | None, image: str) -> Any:
        ctx = _context(FakeFacade())
        ctx.image_ref = cast(Any, SimpleNamespace(short=image))
        ctx._agent_sock_path = None
        ctx.local_config = cast(
            Any,
            SimpleNamespace(
                container=SimpleNamespace(
                    scratch_root=tmp_path,
                    scratch_type=ScratchType.HOSTDIR,
                    deeplearning_samples_path=samples,
                ),
                debug=SimpleNamespace(coredump=SimpleNamespace(enabled=False)),
                agent=SimpleNamespace(ipc_base_path=tmp_path / "ipc"),
            ),
        )
        return ctx

    async def _targets(self, ctx: Any) -> set[str]:
        return {str(m.target) for m in await ctx.get_intrinsic_mounts()}

    async def test_a_dl_image_gets_the_samples(self, tmp_path: Path) -> None:
        samples = tmp_path / "samples"
        samples.mkdir()
        ctx = self._ctx(tmp_path, samples=str(samples), image="pytorch:2.1")
        assert "/home/work/samples" in await self._targets(ctx)

    async def test_a_non_dl_image_does_not(self, tmp_path: Path) -> None:
        samples = tmp_path / "samples"
        samples.mkdir()
        ctx = self._ctx(tmp_path, samples=str(samples), image="python:3.13")
        assert "/home/work/samples" not in await self._targets(ctx)

    async def test_unconfigured_means_no_samples(self, tmp_path: Path) -> None:
        # Which is also what a Docker node without the volume gets.
        ctx = self._ctx(tmp_path, samples=None, image="tensorflow:2.15")
        assert "/home/work/samples" not in await self._targets(ctx)

    async def test_a_path_that_is_not_there_does_not_break_the_kernel(self, tmp_path: Path) -> None:
        # Bind-mounting a missing source would fail the container creation outright.
        ctx = self._ctx(tmp_path, samples=str(tmp_path / "nope"), image="tensorflow:2.15")
        assert "/home/work/samples" not in await self._targets(ctx)

    async def test_it_is_read_only(self, tmp_path: Path) -> None:
        samples = tmp_path / "samples"
        samples.mkdir()
        ctx = self._ctx(tmp_path, samples=str(samples), image="keras:3")
        mount = next(
            m for m in await ctx.get_intrinsic_mounts() if str(m.target) == "/home/work/samples"
        )
        assert mount.permission == MountPermission.READ_ONLY


class TestReserveHostPortsBinding:
    """The published-port host address is chosen per service: a protected service (ttyd on a
    storage node) binds to loopback so it cannot be reached off-node; an ordinary service binds to
    the configured bind-host. The DNAT rule then confines itself with `-d`. Before this,
    protected_services was defined but never consulted and every service was DNAT'd on every
    address."""

    def _ctx(self, *, rg: Any, bind_host: str) -> Any:
        ctx = _context(FakeFacade())
        ctx.local_config = cast(
            Any,
            SimpleNamespace(
                agent=SimpleNamespace(scaling_group_type=rg),
                container=SimpleNamespace(bind_host=bind_host),
            ),
        )
        ctx._port_pool = PortPool((30000, 30100), 0.0)
        return ctx

    def _reserve(self, ctx: Any, service_ports: list[Any]) -> dict[int, str | None]:
        ctx._reserve_host_ports(service_ports)
        # container_port -> host_ip, so a test can assert per service without depending on ordering
        return {container_port: host_ip for _hp, container_port, host_ip in ctx._host_port_map}

    def test_protected_service_binds_loopback_on_storage(self) -> None:
        ctx = self._ctx(rg=ResourceGroupType.STORAGE, bind_host="10.0.0.5")
        sports = [
            {"name": "ttyd", "container_ports": (7681,)},
            {"name": "jupyter", "container_ports": (8080,)},
        ]
        by_port = self._reserve(ctx, sports)
        assert by_port[7681] == "127.0.0.1"  # protected -> loopback, even with a bind_host set
        assert by_port[8080] == "10.0.0.5"  # ordinary -> the configured bind_host

    def test_ordinary_service_binds_the_configured_host(self) -> None:
        ctx = self._ctx(rg=ResourceGroupType.COMPUTE, bind_host="10.0.0.5")
        by_port = self._reserve(ctx, [{"name": "jupyter", "container_ports": (8080,)}])
        assert by_port[8080] == "10.0.0.5"

    def test_empty_bind_host_means_every_address(self) -> None:
        # The default. bind_host "" -> None -> the DNAT falls back to --dst-type LOCAL, unchanged
        # from before an operator sets bind-host.
        ctx = self._ctx(rg=ResourceGroupType.COMPUTE, bind_host="")
        by_port = self._reserve(ctx, [{"name": "jupyter", "container_ports": (8080,)}])
        assert by_port[8080] is None

    def test_ttyd_is_not_protected_on_compute(self) -> None:
        # Only storage protects ttyd; on compute it is an ordinary service.
        ctx = self._ctx(rg=ResourceGroupType.COMPUTE, bind_host="10.0.0.5")
        by_port = self._reserve(ctx, [{"name": "ttyd", "container_ports": (7681,)}])
        assert by_port[7681] == "10.0.0.5"


_SINGLE_NODE = {"mode": ClusterMode.SINGLE_NODE}
_MULTI_NODE = {"mode": ClusterMode.MULTI_NODE}


class TestEtcHosts:
    """containerd/runc synthesizes no /etc/hosts and provides no cluster DNS. The agent must write
    the file itself: localhost + the kernel's own name for every session, and deterministic peer
    addresses for a single-node cluster (there is no manager-assigned IP to fall back on)."""

    def _ctx(self, tmp_path: Path, *, subnet: str | None = "172.30.0.0/26") -> Any:
        ctx = _context(FakeFacade())
        (tmp_path / "config").mkdir(parents=True, exist_ok=True)
        ctx._scratch_dir = tmp_path
        ctx._session_id = "sess-abc"

        async def local_subnet_of(session_id: str) -> str | None:
            return subnet

        ctx._session_network = cast(Any, SimpleNamespace(local_subnet_of=local_subnet_of))
        return ctx

    def _hosts(self, tmp_path: Path) -> dict[str, str]:
        # hostname -> ip, parsed back from the written file (skip the ipv6 localhost line)
        out: dict[str, str] = {}
        for line in (tmp_path / "config" / "hosts").read_text().splitlines():
            ip, _, name = line.partition("\t")
            if name and not name.startswith("localhost"):
                out[name] = ip
        return out

    async def test_an_ordinary_session_still_gets_localhost_and_its_own_name(
        self, tmp_path: Path
    ) -> None:
        ctx = self._ctx(tmp_path)
        env = {"BACKENDAI_CLUSTER_HOST": "main1"}  # a lone kernel: no CLUSTER_HOSTS list
        peers, static_ip = await ctx._peer_host_map(cast(Any, _SINGLE_NODE), env)
        assert peers == {} and static_ip is None
        mount = ctx._write_etc_hosts(peers, env)
        assert mount is not None and str(mount.target) == "/etc/hosts"
        text = (tmp_path / "config" / "hosts").read_text()
        assert "127.0.0.1\tlocalhost" in text
        assert "main1" in text  # own hostname resolves (to loopback, absent a peer map)

    async def test_single_node_cluster_lays_out_deterministic_peers(self, tmp_path: Path) -> None:
        ctx = self._ctx(tmp_path)
        env = {
            "BACKENDAI_CLUSTER_HOSTS": "main1,sub1,sub2",
            "BACKENDAI_CLUSTER_HOST": "sub1",
        }
        peers, static_ip = await ctx._peer_host_map(cast(Any, _SINGLE_NODE), env)

        assert peers == {"main1": "172.30.0.2", "sub1": "172.30.0.3", "sub2": "172.30.0.4"}
        assert static_ip == "172.30.0.3"  # this kernel (sub1) is pinned at its own entry

        ctx._write_etc_hosts(peers, env)
        written = self._hosts(tmp_path)
        assert written["main1"] == "172.30.0.2"
        assert written["sub2"] == "172.30.0.4"
        assert written["sub1"] == "172.30.0.3"  # own name -> own pinned IP, not loopback

    async def test_multi_node_uses_the_managers_cluster_hosts_verbatim(
        self, tmp_path: Path
    ) -> None:
        # Overlay sessions have central IPs; the agent must not re-lay them out.
        ctx = self._ctx(tmp_path)
        cluster_info = {"cluster_hosts": {"main1": "10.128.5.2", "sub1": "10.128.5.3"}}
        env = {"BACKENDAI_CLUSTER_HOST": "main1"}
        peers, static_ip = await ctx._peer_host_map(cast(Any, cluster_info), env)
        assert peers == {"main1": "10.128.5.2", "sub1": "10.128.5.3"}
        assert static_ip is None  # the overlay attach already put this kernel at its address

        # ...and the kernel's OWN name must resolve to its overlay address, not to loopback:
        # torchrun's master binds c10d at whatever `main1` resolves to on the master itself.
        ctx._write_etc_hosts(peers, env)
        written = self._hosts(tmp_path)
        assert written["main1"] == "10.128.5.2"
        assert written["sub1"] == "10.128.5.3"

    async def test_helper_mode_skips_peer_layout(self, tmp_path: Path) -> None:
        # Under a helper the subnet is None (the helper owns the pool); fall back to baseline only.
        ctx = self._ctx(tmp_path, subnet=None)
        env = {"BACKENDAI_CLUSTER_HOSTS": "main1,sub1", "BACKENDAI_CLUSTER_HOST": "main1"}
        peers, own_ip = await ctx._peer_host_map(cast(Any, _SINGLE_NODE), env)
        assert peers == {} and own_ip is None

    async def test_a_multi_node_session_is_never_laid_out_locally(self, tmp_path: Path) -> None:
        # An empty cluster_hosts does NOT mean single-node: a MULTI_NODE session on a PERSISTENT
        # network gets the bridge backend and no manager-assigned addresses either. Laying its peers
        # out in THIS node's /26 would give every node a different map, naming addresses that exist
        # only on its own bridge — worse than no map at all.
        ctx = self._ctx(tmp_path)
        env = {"BACKENDAI_CLUSTER_HOSTS": "main1,sub1", "BACKENDAI_CLUSTER_HOST": "sub1"}
        peers, static_ip = await ctx._peer_host_map(cast(Any, _MULTI_NODE), env)
        assert peers == {} and static_ip is None

    async def test_a_kernel_missing_from_its_own_peer_list_is_refused(self, tmp_path: Path) -> None:
        # No pin would be computed, so the kernel would take the first free address — which is the
        # one the map hands peers[0] — and steal it from the peer pinned there. Fail instead.
        ctx = self._ctx(tmp_path)
        env = {"BACKENDAI_CLUSTER_HOSTS": "main1,sub1", "BACKENDAI_CLUSTER_HOST": "sub9"}
        with pytest.raises(ContainerCreationError):
            await ctx._peer_host_map(cast(Any, _SINGLE_NODE), env)
