"""Unit tests for ContainerdKernelCreationContext network lifecycle.

The heavy AbstractKernelCreationContext.__init__ is bypassed via __new__ + manual field
injection so the lifecycle methods can be tested in isolation against a fake facade.
"""

from typing import Any, cast

import pytest

from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext
from ai.backend.agent.containerd.orchestrator import LaunchResult
from ai.backend.agent.containerd.runtime import TaskHandle
from ai.backend.common.network.types import (
    AttachKind,
    EndpointPlan,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)

_VXLAN_NC = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4097, "mtu": 1450}


class FakeFacade:
    def __init__(self) -> None:
        self.ensured: list[tuple[str, dict[str, Any]]] = []
        self.started: list[tuple[str, str]] = []

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
        self, session_id: str, container_id: str, *, meta: Any, kernel_config: Any, cluster_info: Any
    ) -> LaunchResult:
        self.started.append((session_id, container_id))
        plan = EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI, interface_name="baimulti0",
                    role=NetworkRole.OVERLAY, ip="10.128.5.7", cni_config={},
                )
            ]
        )
        return LaunchResult(handle=TaskHandle(container_id=container_id, pid=555), plan=plan)


def _context(facade: FakeFacade) -> ContainerdKernelCreationContext:
    ctx = ContainerdKernelCreationContext.__new__(ContainerdKernelCreationContext)
    ctx._session_network = cast(Any, facade)
    ctx._session_id = "sess-abc"
    ctx._container_id = "kern-123"
    ctx._net_meta = None
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


class TestStartContainer:
    async def test_requires_apply_network_first(self) -> None:
        ctx = _context(FakeFacade())  # _net_meta is None
        with pytest.raises(RuntimeError):
            await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))

    async def test_starts_and_reports_overlay_host(self) -> None:
        facade = FakeFacade()
        ctx = _context(facade)
        await ctx.apply_network(cast(Any, {"network_config": _VXLAN_NC}))
        result = await ctx.start_container(cast(Any, None), [], None, [], cast(Any, {}))
        assert facade.started == [("sess-abc", "kern-123")]
        assert result["kernel_host"] == "10.128.5.7"  # overlay IP
        assert result["task_pid"] == 555
        assert result["container_id"] == "kern-123"
