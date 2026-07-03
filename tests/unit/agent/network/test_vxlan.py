from collections.abc import Sequence
from typing import cast

import pytest

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.network.backends.vxlan import (
    OVERLAY_IFNAME,
    VxlanNetworkPlugin,
    bridge_dev,
    bridge_link_add_args,
    fdb_append_args,
    fdb_del_args,
    local_bridge_dev,
    local_cni_config,
    overlay_cni_config,
    vxlan_dev,
    vxlan_link_add_args,
)
from ai.backend.common.network.types import (
    Member,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)
from ai.backend.common.types import ClusterInfo, KernelCreationConfig

_META = SessionNetMeta(
    session_id="s1",
    subnet="10.128.5.0/24",
    backend=NetworkBackendKind.VXLAN,
    mtu=1450,
    vni=4097,
)
_SELF = Member(agent_id="a1", host_ip="10.0.0.1", vtep_ip="10.0.0.1")
_PEER = Member(agent_id="a2", host_ip="10.0.0.2", vtep_ip="10.0.0.2")


class Recorder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def __call__(self, argv: Sequence[str]) -> None:
        self.calls.append(list(argv))


def _plugin(recorder: Recorder, *, uplink: str = "eth0") -> VxlanNetworkPlugin:
    return VxlanNetworkPlugin({}, {}, uplink=uplink, runner=recorder)


class TestCommandBuilders:
    def test_iface_names_within_limit(self) -> None:
        # Linux interface names must be <= 15 chars, even for the max VNI.
        assert len(vxlan_dev(16777215)) <= 15
        assert len(bridge_dev(16777215)) <= 15

    def test_vxlan_link_add(self) -> None:
        args = vxlan_link_add_args(4097, "eth0")
        assert args[:5] == ["ip", "link", "add", "baivx4097", "type"]
        assert "vxlan" in args and "4097" in args
        assert args[args.index("dev") + 1] == "eth0"
        assert args[args.index("dstport") + 1] == "4789"
        assert "nolearning" in args

    def test_bridge_link_add(self) -> None:
        assert bridge_link_add_args(4097) == ["ip", "link", "add", "baibr4097", "type", "bridge"]

    def test_fdb_append_uses_broadcast_mac_and_peer_dst(self) -> None:
        args = fdb_append_args(4097, "10.0.0.2")
        assert args == [
            "bridge", "fdb", "append", "00:00:00:00:00:00",
            "dev", "baivx4097", "dst", "10.0.0.2",
        ]

    def test_fdb_del_mirrors_append(self) -> None:
        assert fdb_del_args(4097, "10.0.0.2")[2] == "del"


class TestCNIConfig:
    def test_overlay_config_binds_session_bridge_and_subnet(self) -> None:
        conf = overlay_cni_config(_META)
        assert conf["type"] == "bridge"
        assert conf["bridge"] == "baibr4097"
        assert conf["ipam"]["subnet"] == "10.128.5.0/24"
        assert conf["mtu"] == 1450
        assert conf["ipMasq"] is False

    def test_local_config_is_gateway_with_masq(self) -> None:
        conf = local_cni_config("s1", bridge="bailo4097", subnet="172.30.0.0/24")
        assert conf["isDefaultGateway"] is True
        assert conf["ipMasq"] is True
        assert conf["hairpinMode"] is False
        # per-session LOCAL bridge on a node-local subnet (not the stretched overlay)
        assert conf["bridge"] == "bailo4097"
        assert conf["ipam"]["subnet"] == "172.30.0.0/24"
        assert conf["name"] == "bai-local-s1"

    def test_local_bridge_is_per_session_within_ifname_limit(self) -> None:
        assert local_bridge_dev(4097) == "bailo4097"
        assert len(local_bridge_dev(16777215)) <= 15


class TestSetupTeardown:
    async def test_setup_issues_expected_command_sequence(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        assert rec.calls[0] == vxlan_link_add_args(4097, "eth0")
        assert rec.calls[1] == bridge_link_add_args(4097)
        # vxlan enslaved to bridge, then both brought up
        assert ["ip", "link", "set", "baivx4097", "master", "baibr4097"] in rec.calls
        assert ["ip", "link", "set", "baivx4097", "up"] in rec.calls
        assert ["ip", "link", "set", "baibr4097", "up"] in rec.calls

    async def test_setup_rejects_non_vxlan_meta(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        bad = SessionNetMeta(
            session_id="s1", subnet="10.128.5.0/24",
            backend=NetworkBackendKind.HOST_GW, mtu=1500,
        )
        with pytest.raises(ValueError):
            await plugin.setup_session_network(bad, _SELF)

    async def test_teardown_deletes_bridge_and_vxlan(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert ["ip", "link", "del", "baibr4097"] in rec.calls
        assert ["ip", "link", "del", "baivx4097"] in rec.calls

    async def test_teardown_also_deletes_local_bridge(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert ["ip", "link", "del", local_bridge_dev(4097)] in rec.calls

    async def test_teardown_unknown_session_is_noop(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.teardown_session_network("nope")
        assert rec.calls == []


class TestLocalSubnetAllocation:
    def test_idempotent_per_session_and_distinct_across_sessions(self) -> None:
        plugin = _plugin(Recorder())
        a1 = plugin._alloc_local_subnet("sA")
        a2 = plugin._alloc_local_subnet("sA")
        b = plugin._alloc_local_subnet("sB")
        assert a1 == a2  # idempotent
        assert a1 != b  # distinct sessions -> distinct node-local subnets
        assert a1.startswith("172.30.") and b.startswith("172.30.")

    async def test_local_subnet_freed_on_teardown(self) -> None:
        plugin = _plugin(Recorder())
        await plugin.setup_session_network(_META, _SELF)
        first = plugin._alloc_local_subnet("s1")
        await plugin.teardown_session_network("s1")
        # after teardown the block is reusable by a new session
        reused = plugin._alloc_local_subnet("s-new")
        assert reused == first


class TestPeers:
    async def test_add_peer_appends_fdb_for_peer_vtep(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        rec.calls.clear()
        await plugin.add_peer("s1", _PEER)
        assert rec.calls == [fdb_append_args(4097, "10.0.0.2")]

    async def test_add_peer_without_setup_is_noop(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.add_peer("s1", _PEER)
        assert rec.calls == []

    async def test_del_peer_removes_fdb(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        rec.calls.clear()
        await plugin.del_peer("s1", _PEER)
        assert rec.calls == [fdb_del_args(4097, "10.0.0.2")]


class TestAttachEndpoint:
    async def test_returns_local_default_route_and_overlay(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        plan = await plugin.attach_endpoint(
            cast(KernelCreationConfig, {}), cast(ClusterInfo, {}), meta=_META
        )
        overlay = plan.overlay()
        assert overlay is not None
        assert overlay.interface_name == OVERLAY_IFNAME
        assert overlay.cni_config is not None
        assert overlay.cni_config["bridge"] == "baibr4097"
        local = plan.local()
        assert local.is_default_route is True
        assert local.role is NetworkRole.LOCAL
        # per-session LOCAL bridge on a node-local subnet (not the stretched overlay)
        assert local.cni_config is not None
        assert local.cni_config["bridge"] == local_bridge_dev(4097)
        assert local.cni_config["ipam"]["subnet"].startswith("172.30.")
