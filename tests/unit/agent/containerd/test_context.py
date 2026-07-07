"""Unit tests for ContainerdKernelCreationContext network lifecycle.

The heavy AbstractKernelCreationContext.__init__ is bypassed via __new__ + manual field
injection so the lifecycle methods can be tested in isolation against a fake facade.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext
from ai.backend.agent.containerd.orchestrator import LaunchResult
from ai.backend.agent.containerd.runtime import TaskHandle
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
        self.local_created: list[str] = []
        self.local_started: list[str] = []

    async def create_local_container(
        self, session_id: str, container_id: str, *, image_ref: str, command: Any, oci_spec: Any
    ) -> None:
        self.local_created.append(container_id)

    async def start_local_container(self, container_id: str) -> tuple[int, str | None]:
        self.local_started.append(container_id)
        return 777, "172.20.0.5"

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


def _context(facade: FakeFacade) -> ContainerdKernelCreationContext:
    ctx = ContainerdKernelCreationContext.__new__(ContainerdKernelCreationContext)
    ctx._session_network = cast(Any, facade)
    ctx._session_id = "sess-abc"
    ctx._container_id = "kern-123"
    ctx._net_meta = None
    ctx._oci_mounts = []
    ctx._scratch_dir = None
    ctx._pending_spec = SimpleNamespace(
        image_ref="img:1", oci_spec={}, command=["/opt/kernel/entrypoint.sh"]
    )
    ctx.kernel_config = cast(Any, {})
    return ctx


class TestApplyNetwork:
    async def test_sets_up_session_when_backend_present(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        assert facade.ensured == [("sess-abc", _VXLAN_NC)]
        assert ctx._net_meta is not None
        assert ctx._net_meta.vni == 4097

    async def test_noop_without_backend(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(cast(Any, {"network_config": {}}))
        assert facade.ensured == []
        assert ctx._net_meta is None

    async def test_noop_without_network_config(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(cast(Any, {}))
        assert facade.ensured == []


class TestScratchAndMounts:
    async def test_prepare_scratch_creates_config_and_work(self, tmp_path: Path) -> None:
        ctx = _context(FakeFacade())
        ctx.local_config = cast(
            Any, SimpleNamespace(container=SimpleNamespace(scratch_root=tmp_path))
        )
        await ctx.prepare_scratch()
        assert (tmp_path / "kern-123" / "config").is_dir()
        assert (tmp_path / "kern-123" / "work").is_dir()
        assert ctx._scratch_dir == (tmp_path / "kern-123").resolve()

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
    async def test_single_node_uses_bridge_and_reports_container_ip(self) -> None:
        # no apply_network / _net_meta -> single-node: bridge network, kernel_host = container IP
        facade = FakeFacade()
        ctx = _context(facade)
        result = await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert facade.local_started == ["kern-123"]
        assert result["kernel_host"] == "172.20.0.5"  # container bridge IP
        assert result["task_pid"] == 777

    async def test_starts_and_reports_local_host(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        result = await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert facade.started == [("sess-abc", "kern-123")]
        # kernel_host is the LOCAL IP (host-reachable), not the overlay IP
        assert result["kernel_host"] == "172.30.1.2"
        assert result["task_pid"] == 555
        assert result["container_id"] == "kern-123"
