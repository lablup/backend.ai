import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any, cast, override

import pytest

from ai.backend.agent.errors.network import (
    OverlayAddressNotAssigned,
    OverlayEncryptionUnavailable,
    OverlayMtuTooLarge,
)
from ai.backend.agent.network.backends import vxlan as vx
from ai.backend.agent.network.backends.vxlan import (
    OVERLAY_IFNAME,
    VxlanNetworkPlugin,
    bridge_dev,
    bridge_link_add_args,
    fdb_append_args,
    fdb_del_args,
    fdb_replace_args,
    forward_accept_add_args,
    forward_accept_check_args,
    forward_accept_del_args,
    local_bridge_dev,
    local_cni_config,
    local_ip_capability_args,
    neigh_del_args,
    neigh_replace_args,
    overlay_cni_config,
    overlay_mac_capability_args,
    vxlan_dev,
    vxlan_link_add_args,
    xfrm_add_args,
    xfrm_del_args,
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
_KEY = "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
_ENC_META = SessionNetMeta(
    session_id="s1",
    subnet="10.128.5.0/24",
    backend=NetworkBackendKind.VXLAN,
    mtu=1412,
    vni=4097,
    encryption_key=_KEY,
)


class Recorder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def __call__(self, argv: Sequence[str]) -> None:
        self.calls.append(list(argv))


def _mtu_probe(value: int | None) -> Callable[[str], Awaitable[int | None]]:
    async def probe(uplink: str) -> int | None:
        return value

    return probe


class _ReachRecorder:
    """A stand-in for the ARP reach probe: records who was probed, answers as told."""

    def __init__(self, answer: bool | None = True) -> None:
        self.answer = answer
        self.calls: list[tuple[str, str, str]] = []

    async def __call__(self, bridge: str, ip: str, mac: str) -> bool | None:
        self.calls.append((bridge, ip, mac))
        return self.answer


def _plugin(
    recorder: Recorder,
    *,
    uplink: str = "eth0",
    underlay: int | None = 1500,
    reach: _ReachRecorder | None = None,
) -> VxlanNetworkPlugin:
    return VxlanNetworkPlugin(
        {},
        {},
        uplink=uplink,
        runner=recorder,
        mtu_probe=_mtu_probe(underlay),
        # Default to a probe that answers, so tests unrelated to reachability neither spawn a real
        # AF_PACKET probe nor leave a retry loop running.
        reach_probe=reach or _ReachRecorder(True),
    )


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

    def test_mtu_is_a_generic_link_property_before_type(self) -> None:
        # `mtu` MUST precede `type vxlan`: iproute2 parses the token after `type vxlan` as a vxlan
        # sub-option, so `... type vxlan id N ... mtu M` errors out. Verified against live iproute2.
        vargs = vxlan_link_add_args(4097, "eth0", mtu=1450)
        assert vargs[vargs.index("mtu") + 1] == "1450"
        assert vargs.index("mtu") < vargs.index("type")
        bargs = bridge_link_add_args(4097, mtu=1450)
        assert bargs[bargs.index("mtu") + 1] == "1450"
        assert bargs.index("mtu") < bargs.index("type")

    def test_no_mtu_by_default(self) -> None:
        assert "mtu" not in vxlan_link_add_args(4097, "eth0")
        assert "mtu" not in bridge_link_add_args(4097)

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
        # deterministic MAC pinned via the STANDARD ``mac`` capability, not a non-standard top-level
        # key a real CNI binary would drop. The value is supplied out-of-band as a capability arg.
        assert conf["capabilities"] == {"mac": True}
        assert "mac" not in conf

    def test_overlay_mac_capability_arg_is_the_deterministic_mac(self) -> None:
        assert overlay_mac_capability_args("10.128.5.7") == {"mac": "02:42:0a:80:05:07"}

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
        # no pin requested -> no capability declared, and never the non-standard requested_ip key
        assert "capabilities" not in conf
        assert "requested_ip" not in conf["ipam"]

    def test_local_config_declares_ips_capability_when_pinned(self) -> None:
        conf = local_cni_config(
            "s1", bridge="bailo4097", subnet="172.30.0.0/24", static_ip="172.30.0.42"
        )
        # pin expressed as the STANDARD ``ips`` capability, not ipam.requested_ip
        assert conf["capabilities"] == {"ips": True}
        assert "requested_ip" not in conf["ipam"]
        assert conf["ipam"]["type"] == "host-local"  # keeps the pool + gateway + MASQ

    def test_local_ip_capability_arg_is_a_cidr_in_the_subnet(self) -> None:
        assert local_ip_capability_args("172.30.0.0/24", "172.30.0.42") == {
            "ips": ["172.30.0.42/24"]
        }

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
        assert vxlan_link_add_args(4097, "eth0", mtu=1450) in rec.calls
        assert bridge_link_add_args(4097, mtu=1450) in rec.calls
        # deletes come before the add of the same device
        assert rec.calls.index(["ip", "link", "del", "baivx4097"]) < rec.calls.index(
            vxlan_link_add_args(4097, "eth0", mtu=1450)
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
        assert vxlan_link_add_args(4097, "eth0", mtu=1450) in rec.calls

    async def test_setup_rejects_non_vxlan_meta(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        bad = SessionNetMeta(
            session_id="s1",
            subnet="10.128.5.0/24",
            backend=NetworkBackendKind.BRIDGE,
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


class TestForwardAccept:
    """On a host with br_netfilter + a DROP FORWARD policy (Docker/kube-proxy co-hosted, or a
    hardened host), bridged overlay frames traverse iptables FORWARD and are dropped, silently
    killing the overlay. setup must install a FORWARD-ACCEPT for the overlay bridge; teardown
    must remove it."""

    async def test_setup_installs_forward_accept_when_absent(self) -> None:
        # iptables -C fails when the rule is absent (as the real runner reports it); the plugin
        # must then add it.
        class _AbsentRuleRunner(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                if list(argv[:2]) == ["iptables", "-C"]:
                    raise RuntimeError("iptables: Bad rule (does a matching rule exist?)")

        rec = _AbsentRuleRunner()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        assert forward_accept_add_args(4097) in rec.calls
        # and it is scoped to the overlay bridge's own intra-bridge path
        assert forward_accept_add_args(4097) == [
            "iptables",
            "-I",
            "FORWARD",
            "-i",
            "baibr4097",
            "-o",
            "baibr4097",
            "-j",
            "ACCEPT",
        ]

    async def test_setup_does_not_duplicate_when_already_present(self) -> None:
        # a plain runner reports iptables -C success (rule present) -> no add.
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        assert forward_accept_check_args(4097) in rec.calls
        assert forward_accept_add_args(4097) not in rec.calls

    async def test_setup_survives_missing_iptables(self) -> None:
        class _NoIptablesRunner(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                if argv and argv[0] == "iptables":
                    raise FileNotFoundError("iptables not installed")
                await super().__call__(argv)

        plugin = _plugin(_NoIptablesRunner())
        await plugin.setup_session_network(_META, _SELF)  # must not raise

    async def test_teardown_removes_forward_accept(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert forward_accept_del_args(4097) in rec.calls


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
            {},
            {},
            runner=Recorder(),
            local_subnets=LocalSubnetAllocator(local_subnet_state_dir),
            mtu_probe=_mtu_probe(1500),
            reach_probe=_ReachRecorder(True),
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


class TestEncryptionBuilders:
    def test_spi_is_directional_and_agrees_across_ends(self) -> None:
        # A's out-SA (src=A,dst=B) and B's in-SA (both computed as src=A,dst=B) must be identical,
        # and the reverse direction must differ — otherwise the two ends cannot match SAs.
        out = xfrm_add_args("10.0.0.1", "10.0.0.2", 4097, _KEY)
        # state[0] is the out SA src=self dst=peer; extract its spi
        state_out = out[0]
        spi_ab = state_out[state_out.index("spi") + 1]
        rev = xfrm_add_args("10.0.0.2", "10.0.0.1", 4097, _KEY)
        # rev's in-SA is state[1]: src=self(=.1) dst=peer... from .2's perspective the in SA is
        # src=.1 dst=.2 — same directed pair as A's out SA, so same SPI.
        state_in_from_b = rev[1]
        spi_from_b = state_in_from_b[state_in_from_b.index("spi") + 1]
        assert spi_ab == spi_from_b

    def test_aead_key_appends_derived_salt(self) -> None:
        # rfc4106 needs key(32B)+salt(4B); the key portion is the raw session key, salt is derived.
        out = xfrm_add_args("10.0.0.1", "10.0.0.2", 4097, _KEY)
        aead_key = out[0][out[0].index("aead") + 2]
        assert aead_key.startswith("0x" + _KEY)
        assert len(aead_key) == len("0x") + 64 + 8  # 32B key + 4B salt, hex

    def test_add_builds_two_states_and_two_policies(self) -> None:
        out = xfrm_add_args("10.0.0.1", "10.0.0.2", 4097, _KEY)
        kinds = [(a[1], a[2]) for a in out]  # ("xfrm", "state"|"policy")
        assert kinds == [
            ("xfrm", "state"),
            ("xfrm", "state"),
            ("xfrm", "policy"),
            ("xfrm", "policy"),
        ]
        # policies select the VXLAN UDP port
        for policy in out[2:]:
            assert "dport" in policy and "4789" in policy

    def test_del_matches_add_spis(self) -> None:
        add = xfrm_add_args("10.0.0.1", "10.0.0.2", 4097, _KEY)
        dele = xfrm_del_args("10.0.0.1", "10.0.0.2", 4097)
        add_out_spi = add[0][add[0].index("spi") + 1]
        del_out_spi = dele[0][dele[0].index("spi") + 1]
        assert add_out_spi == del_out_spi


class TestEncryptedPeers:
    async def test_add_peer_programs_xfrm_after_fdb_when_encrypted(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.add_peer("s1", _PEER)
        assert rec.calls == [
            fdb_append_args(4097, "10.0.0.2"),
            *xfrm_add_args("10.0.0.1", "10.0.0.2", 4097, _KEY),
        ]

    async def test_add_peer_no_xfrm_without_key(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)  # plaintext meta
        rec.calls.clear()
        await plugin.add_peer("s1", _PEER)
        assert rec.calls == [fdb_append_args(4097, "10.0.0.2")]

    async def test_del_peer_withdraws_xfrm_before_fdb(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.del_peer("s1", _PEER)
        assert rec.calls == [
            *xfrm_del_args("10.0.0.1", "10.0.0.2", 4097),
            fdb_del_args(4097, "10.0.0.2"),
        ]


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
        # Named after the node-local block INDEX, not the VNI: `local_subnet` documents the index
        # as naming both the device and the subnet its gateway sits on, and the node-wide store
        # keeps two agents from deriving the same one. Naming the device off the VNI put it
        # outside that guarantee and left the device and the address it carries keyed on unrelated
        # numbers -- which only stays safe while the VNI range (4096+) and the index range
        # (0..pool size) do not meet, and `vni_range` is configurable.
        index = await plugin._local_subnets.lookup(_META.session_id)
        assert index is not None
        assert local.cni_config["bridge"] == local_bridge_dev(index)
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
        # and the deterministic MAC rides along as the standard ``mac`` capability arg
        assert overlay.cni_capability_args == {"mac": "02:42:0a:80:05:07"}


class TestVxlanPort:
    def test_link_add_defaults_to_the_iana_port(self) -> None:
        args = vxlan_link_add_args(4097, "eth0")
        assert args[args.index("dstport") + 1] == "4789"

    def test_link_add_honours_a_moved_port(self) -> None:
        args = vxlan_link_add_args(4097, "eth0", dstport=4790)
        assert args[args.index("dstport") + 1] == "4790"

    def test_xfrm_selectors_follow_the_session_port(self) -> None:
        # Both policies select on the VXLAN UDP port; a selector left on 4789 while the device
        # moved would leave the tunnel unencrypted rather than fail loudly.
        policies = [
            a
            for a in xfrm_add_args("1.1.1.1", "2.2.2.2", 7, "ab" * 32, dstport=4790)
            if "policy" in a
        ]
        assert len(policies) == 2
        for args in policies:
            assert args[args.index("dport") + 1] == "4790"
        for args in xfrm_del_args("1.1.1.1", "2.2.2.2", 7, dstport=4790):
            if "policy" in args:
                assert args[args.index("dport") + 1] == "4790"

    async def test_setup_builds_the_device_on_the_session_port(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        moved = SessionNetMeta(
            session_id="s1",
            subnet="10.128.5.0/24",
            backend=NetworkBackendKind.VXLAN,
            mtu=1450,
            vni=4097,
            vxlan_port=4790,
        )
        await plugin.setup_session_network(moved, _SELF)
        add = next(c for c in rec.calls if c[:3] == ["ip", "link", "add"] and "vxlan" in c)
        assert add[add.index("dstport") + 1] == "4790"


class TestOverlayMtuGuard:
    async def test_accepts_an_overlay_that_fits(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec, underlay=1500)
        await plugin.setup_session_network(_META, _SELF)  # 1450 == 1500 - 50
        assert any(c[:3] == ["ip", "link", "add"] for c in rec.calls)

    async def test_refuses_an_overlay_the_underlay_cannot_carry(self) -> None:
        # An encapsulating pod network (measured: flannel/calico vxlan, cilium tunnel) leaves 1450,
        # so the manager's 1450 overlay is 50 bytes too large and would black-hole silently.
        rec = Recorder()
        plugin = _plugin(rec, underlay=1450)
        with pytest.raises(OverlayMtuTooLarge) as excinfo:
            await plugin.setup_session_network(_META, _SELF)
        # The message must carry the value to configure, or the operator is no better off.
        assert "1450" in str(excinfo.value)
        assert not rec.calls, "no device may be built for a session that was refused"

    async def test_encryption_overhead_counts_against_the_ceiling(self) -> None:
        # 1500 - 50 - 38 = 1412 fits exactly; one byte more does not.
        rec = Recorder()
        await _plugin(rec, underlay=1500).setup_session_network(_ENC_META, _SELF)
        too_big = SessionNetMeta(
            session_id="s1",
            subnet="10.128.5.0/24",
            backend=NetworkBackendKind.VXLAN,
            mtu=1413,
            vni=4097,
            encryption_key=_KEY,
        )
        with pytest.raises(OverlayMtuTooLarge):
            await _plugin(Recorder(), underlay=1500).setup_session_network(too_big, _SELF)

    async def test_unmeasurable_underlay_does_not_refuse(self) -> None:
        # A node whose MTU cannot be read must not lose every session to the guard.
        rec = Recorder()
        plugin = _plugin(rec, underlay=None)
        await plugin.setup_session_network(_META, _SELF)
        assert any(c[:3] == ["ip", "link", "add"] for c in rec.calls)

    async def test_adopt_warns_but_keeps_a_live_session(self) -> None:
        # Restart recovery: the devices are already up and carrying traffic. Refusing here would
        # kill running sessions because the pod network changed under a restarting agent.
        rec = Recorder()
        plugin = _plugin(rec, underlay=1450)
        await plugin.adopt_session_network(_META, _SELF)
        assert plugin._sessions["s1"] is _META


class TestOverlayReachProbe:
    async def _drain(self, plugin: VxlanNetworkPlugin, session_id: str) -> None:
        for task in list(plugin._reach_tasks.get(session_id, set())):
            await task

    async def test_remote_endpoint_is_probed_over_the_session_bridge(self) -> None:
        reach = _ReachRecorder(True)
        plugin = _plugin(Recorder(), reach=reach)
        await plugin.setup_session_network(_META, _SELF)
        await plugin.add_endpoint(
            "s1", ip="10.128.5.9", mac="02:42:0a:80:05:09", vtep_ip="10.0.0.2"
        )
        await self._drain(plugin, "s1")
        assert reach.calls == [(bridge_dev(4097), "10.128.5.9", "02:42:0a:80:05:09")]

    async def test_local_endpoint_is_not_probed(self) -> None:
        # A local endpoint never crosses the tunnel, so probing it would prove nothing about the
        # thing that fails silently -- and would fail on its own for unrelated reasons.
        reach = _ReachRecorder(True)
        plugin = _plugin(Recorder(), reach=reach)
        await plugin.setup_session_network(_META, _SELF)  # _SELF.vtep_ip == 10.0.0.1
        await plugin.add_endpoint(
            "s1", ip="10.128.5.1", mac="02:42:0a:80:05:01", vtep_ip="10.0.0.1"
        )
        await self._drain(plugin, "s1")
        assert reach.calls == []

    async def test_unanswered_probe_is_retried_then_reported(
        self, monkeypatch: Any, caplog: Any
    ) -> None:
        # This is the Calico case: devices up, FDB programmed, nothing crosses.
        monkeypatch.setattr(vx, "_REACH_RETRY_DELAY_SEC", 0)
        reach = _ReachRecorder(False)
        plugin = _plugin(Recorder(), reach=reach)
        await plugin.setup_session_network(_META, _SELF)
        with caplog.at_level(logging.ERROR):
            await plugin.add_endpoint(
                "s1", ip="10.128.5.9", mac="02:42:0a:80:05:09", vtep_ip="10.0.0.2"
            )
            await self._drain(plugin, "s1")
        assert len(reach.calls) == vx._REACH_ATTEMPTS
        assert any("carries no traffic" in r.message for r in caplog.records)
        # The remedy has to be in the message, or the operator is back to guessing.
        assert any("vxlan-port" in r.message for r in caplog.records)

    async def test_unprobeable_is_not_reported_as_broken(
        self, monkeypatch: Any, caplog: Any
    ) -> None:
        # No CAP_NET_RAW / no such device: a diagnostic that could not run must not be mistaken
        # for a diagnosis, and must not burn the retries either.
        monkeypatch.setattr(vx, "_REACH_RETRY_DELAY_SEC", 0)
        reach = _ReachRecorder(None)
        plugin = _plugin(Recorder(), reach=reach)
        await plugin.setup_session_network(_META, _SELF)
        with caplog.at_level(logging.ERROR):
            await plugin.add_endpoint(
                "s1", ip="10.128.5.9", mac="02:42:0a:80:05:09", vtep_ip="10.0.0.2"
            )
            await self._drain(plugin, "s1")
        assert len(reach.calls) == 1
        assert not [r for r in caplog.records if "carries no traffic" in r.message]

    async def test_teardown_cancels_a_pending_probe(self, monkeypatch: Any) -> None:
        # The bridge is about to be deleted; a probe still retrying against it is pure noise.
        monkeypatch.setattr(vx, "_REACH_RETRY_DELAY_SEC", 30)
        reach = _ReachRecorder(False)
        plugin = _plugin(Recorder(), reach=reach)
        await plugin.setup_session_network(_META, _SELF)
        await plugin.add_endpoint(
            "s1", ip="10.128.5.9", mac="02:42:0a:80:05:09", vtep_ip="10.0.0.2"
        )
        task = next(iter(plugin._reach_tasks["s1"]))
        await asyncio.sleep(0)
        await plugin.teardown_session_network("s1")
        assert task.cancelled() or task.cancelling()
        assert "s1" not in plugin._reach_tasks


class TestXfrmStateVerb:
    """`ip xfrm state update` on an absent SA is ESRCH, so it can never create one.

    Measured on a live encrypted session: every call failed with "RTNETLINK answers: No such
    process", `ip xfrm state count` stayed 0, and the overlay carried plaintext while the manager
    had already taken 38 bytes off the MTU for ESP -- a session that reports encryption and has
    none.
    """

    def test_states_are_added_not_updated(self) -> None:
        cmds = xfrm_add_args("10.0.0.1", "10.0.0.2", 7, "ab" * 32)
        states = [c for c in cmds if c[:3] == ["ip", "xfrm", "state"]]
        assert len(states) == 2
        for c in states:
            assert c[3] == "add", c

    def test_policies_stay_update(self) -> None:
        # XFRM_MSG_UPDPOLICY does create when absent, so the policies need no add/EEXIST dance.
        cmds = xfrm_add_args("10.0.0.1", "10.0.0.2", 7, "ab" * 32)
        policies = [c for c in cmds if c[:3] == ["ip", "xfrm", "policy"]]
        assert len(policies) == 2
        for c in policies:
            assert c[3] == "update", c

    async def test_existing_sa_is_replayed_as_update(self) -> None:
        # Kernel SAs outlive the agent, so a restart re-programs onto one that already exists;
        # `add` is EEXIST there and must fall back rather than fail the session.
        class FailAdd(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                if list(argv[:4]) == ["ip", "xfrm", "state", "add"]:
                    raise RuntimeError("RTNETLINK answers: File exists")

        rec = FailAdd()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.add_peer("s1", _PEER)
        verbs = [c[3] for c in rec.calls if c[:3] == ["ip", "xfrm", "state"]]
        assert verbs.count("add") == 2 and verbs.count("update") == 2, verbs

    async def test_a_non_state_failure_is_not_swallowed(self) -> None:
        class FailPolicy(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                if list(argv[:3]) == ["ip", "xfrm", "policy"]:
                    raise RuntimeError("boom")

        plugin = _plugin(FailPolicy())
        await plugin.setup_session_network(_ENC_META, _SELF)
        with pytest.raises(RuntimeError, match="boom"):
            await plugin.add_peer("s1", _PEER)


class TestEncryptionTeardown:
    """Teardown must unprogram ESP itself; the device delete does not take XFRM with it.

    Measured: after a session, one node still held `SAD 2 / SPD 1+1` pointing at a dead peer pod
    IP while the other was clean, and the next encrypted session on that VTEP pair saw 100% packet
    loss until `ip xfrm state flush`. The SPI is derived from (vni, src, dst), so a reused VNI on
    the same pair recomputes the SAME SPI with a DIFFERENT key -- a stale SA silently eats traffic.
    """

    @staticmethod
    def _xfrm(rec: Recorder) -> list[list[str]]:
        return [c for c in rec.calls if c[:2] == ["ip", "xfrm"]]

    async def test_teardown_deletes_esp_for_a_peer_del_peer_never_saw(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")  # no del_peer: the peer vanished
        deletes = [c for c in self._xfrm(rec) if c[3] == "delete" or c[3] == "del"]
        assert deletes, "teardown left the SA/policy behind"
        assert any(_PEER.vtep_ip in c for c in deletes)

    async def test_teardown_is_quiet_for_a_plaintext_session(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)  # no encryption_key
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert self._xfrm(rec) == []

    async def test_del_peer_then_teardown_does_not_delete_twice(self) -> None:
        # del_peer already cleaned this peer, so teardown has nothing left to do for it.
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        await plugin.del_peer("s1", _PEER)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert self._xfrm(rec) == []

    async def test_a_delete_that_fails_does_not_stop_the_rest(self) -> None:
        # A peer whose entries are already gone must not strand the next peer's.
        class FlakyDelete(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                if list(argv[:4]) == ["ip", "xfrm", "state", "delete"] and _PEER.vtep_ip in argv:
                    raise RuntimeError("RTNETLINK answers: No such process")

        other = Member(agent_id="a3", host_ip="10.0.0.3", vtep_ip="10.0.0.3")
        rec = FlakyDelete()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        await plugin.add_peer("s1", other)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert any(other.vtep_ip in c for c in self._xfrm(rec))


def _enc_meta(session_id: str, vni: int, key: str = _KEY) -> SessionNetMeta:
    return SessionNetMeta(
        session_id=session_id,
        subnet="10.128.5.0/24",
        backend=NetworkBackendKind.VXLAN,
        mtu=1412,
        vni=vni,
        encryption_key=key,
    )


def _policies(rec: Recorder) -> list[list[str]]:
    return [c for c in rec.calls if c[:3] == ["ip", "xfrm", "policy"]]


def _states(rec: Recorder) -> list[list[str]]:
    return [c for c in rec.calls if c[:3] == ["ip", "xfrm", "state"]]


class TestTheEspPolicyIsSharedBetweenSessions:
    """The policy selector is the OUTER packet — src/dst VTEP, udp dport — and the VNI lives inside
    the UDP payload where no XFRM selector reaches it. So two sessions between the same two nodes
    on the same port share one policy, however many SAs they have.

    That is a fact about transport-mode ESP, not a choice, and the danger is what it does to
    teardown: removing the policy with whichever session ends first leaves the others running with
    their SAs intact and nothing selecting them — in clear text, silently.
    """

    async def _two_sessions(self, rec: Recorder) -> VxlanNetworkPlugin:
        plugin = _plugin(rec)
        for session_id, vni in (("s1", 4097), ("s2", 4098)):
            meta = _enc_meta(session_id, vni)
            await plugin.setup_session_network(meta, _SELF)
            await plugin.add_peer(session_id, _PEER)
        return plugin

    async def test_the_second_session_does_not_reinstall_the_policy(self) -> None:
        rec = Recorder()
        await self._two_sessions(rec)

        assert len(_states(rec)) == 4, "each session programs its own SA pair"
        assert len(_policies(rec)) == 2, "but the policy pair is installed once"

    async def test_the_first_teardown_leaves_the_policy_for_the_other(self) -> None:
        rec = Recorder()
        plugin = await self._two_sessions(rec)
        rec.calls.clear()

        await plugin.teardown_session_network("s1")

        assert [c[3] for c in _states(rec)] == ["del", "del"], "its own SAs go"
        assert _policies(rec) == [], "the policy the other session is using stays"

    async def test_the_last_teardown_removes_it(self) -> None:
        rec = Recorder()
        plugin = await self._two_sessions(rec)
        await plugin.teardown_session_network("s1")
        rec.calls.clear()

        await plugin.teardown_session_network("s2")

        assert [c[3] for c in _policies(rec)] == ["del", "del"]

    async def test_a_lone_session_still_removes_it(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()

        await plugin.teardown_session_network("s1")

        assert [c[3] for c in _policies(rec)] == ["del", "del"]

    async def test_a_different_peer_gets_its_own_policy(self) -> None:
        """The sharing is per (self, peer, port) — a second peer is a different tunnel."""
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        await plugin.add_peer("s1", Member(agent_id="a3", host_ip="10.0.0.3", vtep_ip="10.0.0.3"))

        assert len(_policies(rec)) == 4


class TestAnEncryptedSessionOnANodeWithNoVtep:
    """The SAs are keyed on the ordered VTEP pair, so with no local endpoint there is no `src` to
    program them with. This used to warn from `add_peer` and carry on: the session came up, carried
    traffic, and was in clear text with one log line to say so."""

    async def test_setup_refuses_it(self) -> None:
        plugin = _plugin(Recorder())
        headless = Member(agent_id="a1", host_ip="10.0.0.1", vtep_ip=None)

        with pytest.raises(OverlayEncryptionUnavailable, match="usable VTEP"):
            await plugin.setup_session_network(_ENC_META, headless)

    async def test_it_leaves_no_devices_behind(self) -> None:
        """A precondition, so it runs before any side effect."""
        rec = Recorder()
        plugin = _plugin(rec)
        headless = Member(agent_id="a1", host_ip="10.0.0.1", vtep_ip=None)

        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.setup_session_network(_ENC_META, headless)

        assert [c for c in rec.calls if c[:3] == ["ip", "link", "add"]] == []

    async def test_a_plaintext_session_is_unaffected(self) -> None:
        plugin = _plugin(Recorder())
        headless = Member(agent_id="a1", host_ip="10.0.0.1", vtep_ip=None)

        await plugin.setup_session_network(_META, headless)  # does not raise


class TestAPartiallyProgrammedPeerIsStillRecorded:
    """A failure partway through leaves SAs in the kernel. An unrecorded SA is never unprogrammed,
    and the SPI is derived from (vni, src, dst) — so the next session that reuses the VNI on this
    VTEP pair computes the same SPI with a different key and its traffic is dropped wholesale."""

    async def test_the_peer_is_recorded_before_the_commands_run(self) -> None:
        # Fail on the policy, which is the first command with no retry behind it: a failing
        # `state add` is replayed as `update` (the EEXIST path) and would not surface here.
        class _Failing(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                if argv[:3] == ["ip", "xfrm", "policy"]:
                    raise RuntimeError("kernel said no")

        rec = _Failing()
        plugin = _plugin(cast(Recorder, rec))
        await plugin.setup_session_network(_ENC_META, _SELF)

        with pytest.raises(RuntimeError):
            await plugin.add_peer("s1", _PEER)

        assert len(_states(rec)) == 2, "the SA pair did get installed"
        assert plugin._encrypted_peers.get("s1") == {"10.0.0.2"}, (
            "teardown must still know to unprogram what did get installed"
        )
