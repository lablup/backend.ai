from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest

from ai.backend.agent.errors.network import OverlayAddressNotAssigned
from ai.backend.agent.network.backends.vxlan import (
    OVERLAY_IFNAME,
    VxlanNetworkPlugin,
    bridge_dev,
    bridge_link_add_args,
    fdb_append_args,
    fdb_del_args,
    fdb_replace_args,
    local_bridge_dev,
    local_cni_config,
    neigh_del_args,
    neigh_replace_args,
    overlay_cni_config,
    vxlan_dev,
    vxlan_link_add_args,
)
from ai.backend.agent.network.local_subnet import LocalSubnetAllocator
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
            "bridge",
            "fdb",
            "append",
            "00:00:00:00:00:00",
            "dev",
            "baivx4097",
            "dst",
            "10.0.0.2",
        ]

    def test_fdb_del_mirrors_append(self) -> None:
        assert fdb_del_args(4097, "10.0.0.2")[2] == "del"

    def test_fdb_replace_programs_unicast_mac_to_vtep(self) -> None:
        args = fdb_replace_args(4097, "02:42:0a:80:05:02", "10.0.0.2")
        assert args == [
            "bridge",
            "fdb",
            "replace",
            "02:42:0a:80:05:02",
            "dev",
            "baivx4097",
            "dst",
            "10.0.0.2",
        ]

    def test_neigh_replace_programs_permanent_arp_on_bridge(self) -> None:
        args = neigh_replace_args(4097, "10.128.5.2", "02:42:0a:80:05:02")
        assert args == [
            "ip",
            "neigh",
            "replace",
            "10.128.5.2",
            "lladdr",
            "02:42:0a:80:05:02",
            "dev",
            "baibr4097",
            "nud",
            "permanent",
        ]

    def test_neigh_del_targets_bridge(self) -> None:
        assert neigh_del_args(4097, "10.128.5.2") == [
            "ip",
            "neigh",
            "del",
            "10.128.5.2",
            "dev",
            "baibr4097",
        ]


class TestCNIConfig:
    def test_overlay_config_binds_session_bridge_and_uses_static_ipam(self) -> None:
        conf = overlay_cni_config(_META, ip="10.128.5.7")
        assert conf["type"] == "bridge"
        assert conf["bridge"] == "baibr4097"
        assert conf["mtu"] == 1450
        assert conf["ipMasq"] is False
        # central endpoint IP -> static IPAM (disjoint across nodes)
        assert conf["ipam"]["type"] == "static"
        assert conf["ipam"]["addresses"] == [{"address": "10.128.5.7/24"}]
        # deterministic MAC pinned so peers' FDB/ARP (programmed to the same mac_for_ip) match
        assert conf["mac"] == "02:42:0a:80:05:07"

    def test_overlay_config_requires_a_manager_assigned_ip(self) -> None:
        # the overlay subnet is stretched cluster-wide; a node cannot pick locally without
        # colliding, so a missing assignment must fail loudly rather than fall back to host-local
        with pytest.raises(OverlayAddressNotAssigned):
            overlay_cni_config(_META)

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
        # leftover-safe: any pre-existing devices are deleted before (re)creating,
        # including the LOCAL bridge (bailo) whose leftover would carry a stale gateway IP
        assert rec.calls[0] == ["ip", "link", "del", "baibr4097"]
        assert rec.calls[1] == ["ip", "link", "del", "baivx4097"]
        assert ["ip", "link", "del", local_bridge_dev(4097)] in rec.calls
        assert vxlan_link_add_args(4097, "eth0") in rec.calls
        assert bridge_link_add_args(4097) in rec.calls
        # deletes come before the add of the same device
        assert rec.calls.index(["ip", "link", "del", "baivx4097"]) < rec.calls.index(
            vxlan_link_add_args(4097, "eth0")
        )
        # vxlan enslaved to bridge, then both brought up
        assert ["ip", "link", "set", "baivx4097", "master", "baibr4097"] in rec.calls
        assert ["ip", "link", "set", "baivx4097", "up"] in rec.calls
        assert ["ip", "link", "set", "baibr4097", "up"] in rec.calls

    async def test_setup_is_leftover_safe_when_device_exists(self) -> None:
        # A stale device makes `ip link add` fail with 'File exists'; setup must first
        # delete it and then succeed (not raise).
        class FailAddOnce:
            def __init__(self) -> None:
                self.calls: list[list[str]] = []
                self._existing = {"baivx4097", "baibr4097"}

            async def __call__(self, argv: Sequence[str]) -> None:
                argv = list(argv)
                self.calls.append(argv)
                if argv[:3] == ["ip", "link", "del"]:
                    self._existing.discard(argv[3])
                elif argv[:3] == ["ip", "link", "add"] and argv[3] in self._existing:
                    raise RuntimeError(f"command failed (rc=2): {' '.join(argv)}: File exists")

        rec = FailAddOnce()
        plugin = _plugin(cast(Recorder, rec))
        await plugin.setup_session_network(_META, _SELF)  # must not raise
        assert ["ip", "link", "del", "baivx4097"] in rec.calls
        assert vxlan_link_add_args(4097, "eth0") in rec.calls

    async def test_setup_rejects_non_vxlan_meta(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        bad = SessionNetMeta(
            session_id="s1",
            subnet="10.128.5.0/24",
            backend=NetworkBackendKind.HOST_GW,
            mtu=1500,
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
    async def test_idempotent_per_session_and_distinct_across_sessions(self) -> None:
        plugin = _plugin(Recorder())
        a1 = await plugin._local_subnet("sA")
        a2 = await plugin._local_subnet("sA")
        b = await plugin._local_subnet("sB")
        assert a1 == a2  # idempotent
        assert a1 != b  # distinct sessions -> distinct node-local subnets
        assert a1.startswith("172.30.") and b.startswith("172.30.")

    async def test_local_subnet_freed_on_teardown(self) -> None:
        plugin = _plugin(Recorder())
        await plugin.setup_session_network(_META, _SELF)
        first = await plugin._local_subnet("s1")
        await plugin.teardown_session_network("s1")
        # after teardown the block is reusable by a new session
        reused = await plugin._local_subnet("s-new")
        assert reused == first

    async def test_subnet_survives_an_agent_restart(self, local_subnet_state_dir: Path) -> None:
        # A restart drops every in-memory allocation. A surviving session must keep its subnet,
        # and a new session must not be handed the block that session still holds — otherwise
        # two live sessions share a /24 (bridge isolation + the per-subnet MASQ refcount break).
        plugin = _plugin(Recorder())
        held = await plugin._local_subnet("survivor")

        # a fresh agent process: a brand-new allocator over the same on-disk store
        restarted = VxlanNetworkPlugin(
            {}, {}, runner=Recorder(), local_subnets=LocalSubnetAllocator(local_subnet_state_dir)
        )
        assert await restarted._local_subnet("survivor") == held
        assert await restarted._local_subnet("newcomer") != held


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


class TestEndpoints:
    async def test_add_endpoint_programs_unicast_fdb_and_arp(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        rec.calls.clear()
        await plugin.add_endpoint(
            "s1", ip="10.128.5.7", mac="02:42:0a:80:05:07", vtep_ip="10.0.0.2"
        )
        # unicast MAC->VTEP forwarding + permanent ARP => no BUM flood for this endpoint
        assert rec.calls == [
            fdb_replace_args(4097, "02:42:0a:80:05:07", "10.0.0.2"),
            neigh_replace_args(4097, "10.128.5.7", "02:42:0a:80:05:07"),
        ]

    async def test_add_endpoint_without_setup_is_noop(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.add_endpoint(
            "s1", ip="10.128.5.7", mac="02:42:0a:80:05:07", vtep_ip="10.0.0.2"
        )
        assert rec.calls == []

    async def test_del_endpoint_removes_fdb_and_arp(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        rec.calls.clear()
        await plugin.del_endpoint(
            "s1", ip="10.128.5.7", mac="02:42:0a:80:05:07", vtep_ip="10.0.0.2"
        )
        assert rec.calls == [
            fdb_del_args(4097, "10.0.0.2", mac="02:42:0a:80:05:07"),
            neigh_del_args(4097, "10.128.5.7"),
        ]


class TestAttachEndpoint:
    async def test_returns_local_default_route_and_overlay(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        # vxlan is multi-node: the manager always assigns a cluster-unique overlay IP
        plan = await plugin.attach_endpoint(
            cast(KernelCreationConfig, {"cluster_network_ip": "10.128.5.7"}),
            cast(ClusterInfo, {}),
            meta=_META,
        )
        overlay = plan.overlay()
        assert overlay is not None
        assert overlay.interface_name == OVERLAY_IFNAME
        assert overlay.cni_config is not None
        assert overlay.cni_config["bridge"] == "baibr4097"
        assert overlay.cni_config["ipam"]["type"] == "static"
        local = plan.local()
        assert local.is_default_route is True
        assert local.role is NetworkRole.LOCAL
        # per-session LOCAL bridge on a node-local subnet (not the stretched overlay)
        assert local.cni_config is not None
        assert local.cni_config["bridge"] == local_bridge_dev(4097)
        assert local.cni_config["ipam"]["subnet"].startswith("172.30.")

    async def test_overlay_uses_manager_assigned_static_ip(self) -> None:
        plugin = _plugin(Recorder())
        plan = await plugin.attach_endpoint(
            cast(KernelCreationConfig, {"cluster_network_ip": "10.128.5.7"}),
            cast(ClusterInfo, {}),
            meta=_META,
        )
        overlay = plan.overlay()
        assert overlay is not None and overlay.cni_config is not None
        # the manager-assigned IP becomes the container's static overlay address
        assert overlay.cni_config["ipam"]["type"] == "static"
        assert overlay.cni_config["ipam"]["addresses"] == [{"address": "10.128.5.7/24"}]
