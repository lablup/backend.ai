from typing import cast

import pytest

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.plugin.network import ContainerNetworkCapability
from ai.backend.agent.plugin.network_v2 import (
    AbstractNetworkAgentPluginV2,
    NetworkPluginContextV2,
)
from ai.backend.common.network.types import (
    AgentNetworkCaps,
    AttachKind,
    EndpointPlan,
    Member,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)
from ai.backend.common.types import ClusterInfo, KernelCreationConfig

_META = SessionNetMeta(
    session_id="s1",
    subnet="10.128.1.0/24",
    backend=NetworkBackendKind.VXLAN,
    mtu=1450,
    vni=4097,
)


class _CompleteV2Plugin(AbstractNetworkAgentPluginV2[AbstractKernel]):
    """Minimal concrete backend implementing every abstract method."""

    async def init(self, context: object = None) -> None:
        return None

    async def cleanup(self) -> None:
        return None

    async def update_plugin_config(self, plugin_config: object) -> None:
        return None

    async def probe_caps(self) -> AgentNetworkCaps:
        return AgentNetworkCaps(
            tunnel_offload=False, native_routing_ok=True, backends=["vxlan"]
        )

    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        return None

    async def teardown_session_network(self, session_id: str) -> None:
        return None

    async def add_peer(self, session_id: str, peer: Member) -> None:
        return None

    async def del_peer(self, session_id: str, peer: Member) -> None:
        return None

    async def attach_endpoint(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
    ) -> EndpointPlan:
        return EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="eth0",
                    role=NetworkRole.LOCAL,
                    is_default_route=True,
                    cni_config={"type": "bridge", "isGateway": True, "ipMasq": True},
                ),
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="baimulti0",
                    role=NetworkRole.OVERLAY,
                    ip="10.128.1.5",
                    cni_config={"type": "bridge", "vni": meta.vni},
                ),
            ]
        )

    async def detach_endpoint(self, kernel: AbstractKernel) -> None:
        return None


class _IncompleteV2Plugin(AbstractNetworkAgentPluginV2[AbstractKernel]):
    """Missing several abstract methods -> not instantiable."""

    async def probe_caps(self) -> AgentNetworkCaps:
        return AgentNetworkCaps(tunnel_offload=False, native_routing_ok=False)


def _make(plugin_cls: type) -> AbstractNetworkAgentPluginV2[AbstractKernel]:
    return plugin_cls({}, {})


class TestPluginGroup:
    def test_context_plugin_group(self) -> None:
        assert NetworkPluginContextV2.plugin_group == "backendai_network_agent_v2"


class TestAbstractContract:
    def test_incomplete_subclass_is_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            _make(_IncompleteV2Plugin)

    def test_complete_subclass_instantiates(self) -> None:
        plugin = _make(_CompleteV2Plugin)
        assert isinstance(plugin, AbstractNetworkAgentPluginV2)


class TestDefaults:
    async def test_get_capabilities_defaults_to_empty(self) -> None:
        plugin = _make(_CompleteV2Plugin)
        caps: set[ContainerNetworkCapability] = await plugin.get_capabilities()
        assert caps == set()

    async def test_optional_hooks_are_noops_by_default(self) -> None:
        plugin = _make(_CompleteV2Plugin)
        kernel = cast(AbstractKernel, object())
        assert await plugin.prepare_port_forward(kernel, "127.0.0.1", []) is None
        assert await plugin.expose_ports(kernel, "127.0.0.1", []) is None


class TestAttachEndpoint:
    async def test_has_exactly_one_local_and_one_overlay(self) -> None:
        plugin = _make(_CompleteV2Plugin)
        plan = await plugin.attach_endpoint(
            cast(KernelCreationConfig, {}),
            cast(ClusterInfo, {}),
            meta=_META,
        )
        locals_ = [a for a in plan.attachments if a.role is NetworkRole.LOCAL]
        assert len(locals_) == 1
        overlay = plan.overlay()
        assert overlay is not None
        assert overlay.cni_config is not None
        assert overlay.cni_config["vni"] == 4097
        assert overlay.is_default_route is False

    async def test_default_route_is_on_local(self) -> None:
        plugin = _make(_CompleteV2Plugin)
        plan = await plugin.attach_endpoint(
            cast(KernelCreationConfig, {}),
            cast(ClusterInfo, {}),
            meta=_META,
        )
        default_routes = [a for a in plan.attachments if a.is_default_route]
        assert len(default_routes) == 1
        assert default_routes[0].role is NetworkRole.LOCAL
