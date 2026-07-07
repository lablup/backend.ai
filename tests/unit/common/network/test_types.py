import dataclasses

import pytest

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


class TestSessionNetMeta:
    def test_optional_vni_defaults_to_none(self) -> None:
        meta = SessionNetMeta(
            session_id="s1",
            subnet="10.128.1.0/24",
            backend=NetworkBackendKind.HOST_GW,
            mtu=1500,
        )
        assert meta.vni is None
        assert meta.subnet == "10.128.1.0/24"
        assert meta.backend is NetworkBackendKind.HOST_GW

    def test_is_frozen(self) -> None:
        meta = SessionNetMeta(
            session_id="s1",
            subnet="10.128.1.0/24",
            backend=NetworkBackendKind.VXLAN,
            mtu=1450,
            vni=4097,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            meta.mtu = 9000  # type: ignore[misc]


class TestMember:
    def test_optional_fields_default_to_none(self) -> None:
        member = Member(agent_id="a1", host_ip="192.168.0.10")
        assert member.vtep_ip is None
        assert member.ip_range is None

    def test_carries_backend_specific_fields(self) -> None:
        member = Member(
            agent_id="a1",
            host_ip="192.168.0.10",
            vtep_ip="192.168.0.10",
            ip_range="10.128.1.0/26",
        )
        assert member.vtep_ip == "192.168.0.10"
        assert member.ip_range == "10.128.1.0/26"

    def test_etcd_payload_roundtrip_excludes_agent_id(self) -> None:
        # single-sourced on-wire schema shared by agent self-publish and manager pre-seed
        member = Member(agent_id="a1", host_ip="1.2.3.4", vtep_ip="1.2.3.4")
        payload = member.to_etcd_payload()
        assert payload == {"host_ip": "1.2.3.4", "vtep_ip": "1.2.3.4", "ip_range": None}
        assert "agent_id" not in payload  # agent_id is the key, not the value
        assert Member.from_etcd_payload("a1", payload) == member


class TestEnums:
    def test_backend_kind_values(self) -> None:
        assert NetworkBackendKind.VXLAN.value == "vxlan"
        assert NetworkBackendKind.HOST_GW.value == "host-gw"
        assert NetworkBackendKind.WIREGUARD.value == "wireguard"

    def test_attach_kind_values(self) -> None:
        assert AttachKind.CNI.value == "cni"
        assert AttachKind.DOCKER_NETWORK.value == "docker"
        assert AttachKind.HOST_NETNS.value == "netns"


class TestNetworkAttachSpec:
    def test_defaults_leave_configs_unset(self) -> None:
        spec = NetworkAttachSpec(
            kind=AttachKind.CNI,
            interface_name="baimulti0",
            ip="10.128.1.5",
            cni_config={"type": "bridge"},
        )
        assert spec.docker_config is None
        assert spec.netns_ops is None
        assert spec.cni_config == {"type": "bridge"}

    def test_role_defaults_to_local_without_default_route(self) -> None:
        spec = NetworkAttachSpec(kind=AttachKind.CNI, interface_name="eth0")
        assert spec.role is NetworkRole.LOCAL
        assert spec.is_default_route is False
        assert spec.ip is None


class TestEndpointPlan:
    def _multinode_plan(self) -> EndpointPlan:
        return EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="eth0",
                    role=NetworkRole.LOCAL,
                    is_default_route=True,
                ),
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="baimulti0",
                    role=NetworkRole.OVERLAY,
                    ip="10.128.1.5",
                ),
            ]
        )

    def test_local_returns_the_single_local_interface(self) -> None:
        local = self._multinode_plan().local()
        assert local.role is NetworkRole.LOCAL
        assert local.interface_name == "eth0"

    def test_overlay_present_for_multinode(self) -> None:
        overlay = self._multinode_plan().overlay()
        assert overlay is not None
        assert overlay.interface_name == "baimulti0"

    def test_default_route_is_on_local(self) -> None:
        plan = self._multinode_plan()
        default_routes = [a for a in plan.attachments if a.is_default_route]
        assert len(default_routes) == 1
        assert default_routes[0].role is NetworkRole.LOCAL

    def test_single_node_plan_has_local_but_no_overlay(self) -> None:
        plan = EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="eth0",
                    role=NetworkRole.LOCAL,
                    is_default_route=True,
                ),
            ]
        )
        assert plan.local().interface_name == "eth0"
        assert plan.overlay() is None


class TestAgentNetworkCaps:
    def test_backends_default_is_independent_empty_list(self) -> None:
        a = AgentNetworkCaps(tunnel_offload=False, native_routing_ok=True)
        b = AgentNetworkCaps(tunnel_offload=True, native_routing_ok=False)
        assert a.backends == []
        # default_factory must not share a single list instance across instances
        a.backends.append("vxlan")
        assert b.backends == []
