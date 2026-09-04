import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable, Collection, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, cast, override

import pytest

from ai.backend.agent.errors.network import (
    OverlayAddressNotAssigned,
    OverlayEncryptionUnavailable,
    OverlayMtuTooLarge,
    OverlayTeardownIncomplete,
)
from ai.backend.agent.network.backends import vxlan as vx
from ai.backend.agent.network.backends.vxlan import (
    CHAIN_GUARD,
    CHAIN_IN,
    CHAIN_MARK,
    OVERLAY_IFNAME,
    OWNED_CHAINS,
    XFRM_MARK,
    XFRM_REPLAY_WINDOW,
    XFRM_REQID,
    VxlanNetworkPlugin,
    _pair_key,
    bridge_dev,
    bridge_link_add_args,
    egress_guard_add_args,
    egress_guard_del_args,
    fdb_append_args,
    fdb_del_args,
    fdb_replace_args,
    forward_accept_add_args,
    forward_accept_check_args,
    forward_accept_del_args,
    is_absent_error,
    jump_is_first,
    link_down_args,
    link_up_args,
    local_bridge_dev,
    local_cni_config,
    local_ip_capability_args,
    neigh_del_args,
    neigh_replace_args,
    output_mark_add_args,
    output_mark_check_args,
    output_mark_del_args,
    overlay_cni_config,
    overlay_mac_capability_args,
    plaintext_drop_add_args,
    plaintext_drop_check_args,
    plaintext_drop_del_args,
    vxlan_dev,
    vxlan_link_add_args,
    xfrm_add_args,
    xfrm_del_args,
    xfrm_policy_add_args,
    xfrm_state_add_args,
    xfrm_state_del_args,
)
from ai.backend.agent.network.backends.vxlan_security import (
    VxlanSecurityEvent,
    VxlanSecurityState,
    VxlanSecurityStateMachine,
)
from ai.backend.agent.network.local_subnet import LocalSubnetAllocator
from ai.backend.agent.network.pair_journal import PairJournal, pair_key
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
_TEST_GENERATION = 100
_ENC_META = SessionNetMeta(
    session_id="s1",
    subnet="10.128.5.0/24",
    backend=NetworkBackendKind.VXLAN,
    mtu=1412,
    vni=4097,
    encryption_key=_KEY,
)


class Recorder:
    def __init__(self, *, fail_on: Callable[[Sequence[str]], bool] | None = None) -> None:
        self.calls: list[list[str]] = []
        #: Make the matching command fail, for the paths that only exist when one does.
        self.fail_on = fail_on

    async def __call__(self, argv: Sequence[str]) -> None:
        self.calls.append(list(argv))
        if self.fail_on is not None and self.fail_on(argv):
            raise RuntimeError(f"command failed: {' '.join(argv)}")


class _AbsentRuleRecorder(Recorder):
    """A runner whose ``iptables -C`` fails the way the real one reports a missing rule, so the
    idempotent install paths take their add branch."""

    @override
    async def __call__(self, argv: Sequence[str]) -> None:
        await super().__call__(argv)
        if argv and argv[0] == "iptables" and "-C" in argv:
            raise RuntimeError("iptables: Bad rule (does a matching rule exist?)")


class _NoU32Recorder(Recorder):
    """A host whose iptables has no ``u32``/``policy`` match, so the plaintext-drop rule cannot be
    installed. ``blocked`` flips to model the operator fixing it."""

    def __init__(self) -> None:
        super().__init__()
        self.blocked = True

    @override
    async def __call__(self, argv: Sequence[str]) -> None:
        await super().__call__(argv)
        if self.blocked and argv and argv[0] == "iptables" and "--u32" in argv:
            raise RuntimeError("iptables: No chain/target/match by that name")
        if list(argv[:2]) == ["iptables", "-C"]:
            raise RuntimeError("iptables: Bad rule (does a matching rule exist?)")


def _lister(devices: Collection[str]) -> Callable[[], Awaitable[Collection[str]]]:
    async def list_vxlans() -> Collection[str]:
        return devices

    return list_vxlans


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


class _Listing:
    """Stands in for ``iptables -S``. Defaults to a built-in chain whose first rule is our jump,
    so tests unrelated to rule order neither shell out to the host nor see spurious drift."""

    def __init__(self, listing: Callable[[Sequence[str]], str] | None = None) -> None:
        self.calls: list[list[str]] = []
        self._listing = listing

    async def __call__(self, argv: Sequence[str]) -> str:
        self.calls.append(list(argv))
        if self._listing is not None:
            return self._listing(argv)
        table = argv[argv.index("-t") + 1] if "-t" in argv else "filter"
        builtin = argv[argv.index("-S") + 1]
        for owned_table, owned_builtin, chain in OWNED_CHAINS:
            if (owned_table, owned_builtin) == (table, builtin):
                return f"-P {builtin} ACCEPT\n-A {builtin} -j {chain}\n"
        return f"-P {builtin} ACCEPT\n"


@pytest.fixture(autouse=True)
def _isolated_pair_journal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the node-wide ESP pair journal at this test's own directory.

    Its real home is a node-global path shared by every agent on the host, which is the point --
    and exactly why a test must never use it: the claims would outlive the test and the next one
    would see a pair still held by a session that does not exist.
    """
    monkeypatch.setattr(
        "ai.backend.agent.network.pair_journal.DEFAULT_PAIR_JOURNAL_DIR",
        tmp_path / "net-esp-pair",
    )


def _plugin(
    recorder: Recorder,
    *,
    uplink: str = "eth0",
    pair_journal: PairJournal | None = None,
    journal_owner: str | None = None,
    underlay: int | None = 1500,
    reach: _ReachRecorder | None = None,
    vxlans: Collection[str] | None = None,
    key_generation: Callable[[], int] | None = None,
    reader: _Listing | None = None,
) -> VxlanNetworkPlugin:
    return VxlanNetworkPlugin(
        {},
        {},
        uplink=uplink,
        runner=recorder,
        reader=reader or _Listing(),
        pair_journal=pair_journal,
        journal_owner=journal_owner,
        mtu_probe=_mtu_probe(underlay),
        # Default to a probe that answers, so tests unrelated to reachability neither spawn a real
        # AF_PACKET probe nor leave a retry loop running.
        reach_probe=reach or _ReachRecorder(True),
        # Default to a host with no other VXLAN, so tests unrelated to device inventory neither
        # shell out to `ip` nor see a stranger's tunnel.
        vxlan_lister=_lister(vxlans or ()),
        key_generation=key_generation or (lambda: _TEST_GENERATION),
    )


def _initial_xfrm_args(
    self_vtep: str, peer_vtep: str, key: str, *, dstport: int = 4789
) -> list[list[str]]:
    """Commands for first ownership of a pair: clear each bounded SPI slot, fill the
    previous/current/next generations, then select current for outbound traffic."""
    commands: list[list[str]] = []
    for generation in range(_TEST_GENERATION - 1, _TEST_GENERATION + 2):
        commands.extend(xfrm_state_del_args(self_vtep, peer_vtep, generation=generation))
        commands.extend(xfrm_state_add_args(self_vtep, peer_vtep, key, generation=generation))
    commands.extend(
        xfrm_policy_add_args(self_vtep, peer_vtep, dstport=dstport, generation=_TEST_GENERATION)
    )
    return commands


class TestCommandBuilders:
    def test_iface_names_within_limit(self) -> None:
        # Linux interface names must be <= 15 chars, even for the max VNI.
        assert len(vxlan_dev(16777215)) <= 15
        assert len(bridge_dev(16777215)) <= 15

    async def test_failed_xfrm_command_redacts_aead_key_from_command_and_stderr(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        secret = "0x" + "ab" * 36
        argv = [
            "ip",
            "xfrm",
            "state",
            "add",
            "aead",
            "rfc4106(gcm(aes))",
            secret,
            "128",
        ]

        class _FailedProcess:
            returncode = 2

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", f"invalid key {secret}".encode()

        async def _failed_exec(*args: Any, **kwargs: Any) -> _FailedProcess:
            return _FailedProcess()

        monkeypatch.setattr(asyncio, "create_subprocess_exec", _failed_exec)
        with pytest.raises(RuntimeError) as exc_info:
            await vx._run_command(argv)

        message = str(exc_info.value)
        assert secret not in message
        assert message.count("[REDACTED]") == 2

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
    async def test_recovery_preflight_holds_all_owned_vxlan_links_down(self) -> None:
        rec = Recorder()
        plugin = _plugin(
            rec,
            vxlans={vxlan_dev(4097), vxlan_dev(4098), "flannel.1"},
        )

        await plugin.prepare_recovery()

        assert rec.calls == [
            link_down_args(vxlan_dev(4097)),
            link_down_args(vxlan_dev(4098)),
        ]

    async def test_recovery_preflight_reports_any_link_it_cannot_hold_down(self) -> None:
        rec = Recorder(fail_on=lambda argv: list(argv) == link_down_args(vxlan_dev(4097)))
        plugin = _plugin(rec, vxlans={vxlan_dev(4097), vxlan_dev(4098)})

        with pytest.raises(OverlayEncryptionUnavailable, match="baivx4097"):
            await plugin.prepare_recovery()

        assert link_down_args(vxlan_dev(4098)) in rec.calls

    async def test_recovery_preflight_accepts_a_link_that_disappeared(self) -> None:
        inventories = iter(({vxlan_dev(4097): 4789}, {}))

        async def list_vxlans() -> Collection[str]:
            return next(inventories)

        rec = Recorder(fail_on=lambda argv: list(argv) == link_down_args(vxlan_dev(4097)))
        plugin = VxlanNetworkPlugin(
            {},
            {},
            runner=rec,
            local_subnets=LocalSubnetAllocator(),
            mtu_probe=_mtu_probe(1500),
            vxlan_lister=list_vxlans,
            key_generation=lambda: _TEST_GENERATION,
        )

        await plugin.prepare_recovery()

        assert rec.calls == [link_down_args(vxlan_dev(4097))]

    async def test_setup_issues_expected_command_sequence(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        # leftover-safe: any pre-existing devices are deleted before (re)creating,
        # including the LOCAL bridge (bailo) whose leftover would carry a stale gateway IP
        assert rec.calls[0] == ["ip", "link", "del", "baibr4097"]
        assert rec.calls[1] == ["ip", "link", "del", "baivx4097"]
        assert ["ip", "link", "del", local_bridge_dev(4097)] in rec.calls
        assert vxlan_link_add_args(4097, "eth0", local="10.0.0.1", mtu=1450) in rec.calls
        assert bridge_link_add_args(4097, mtu=1450) in rec.calls
        # deletes come before the add of the same device
        assert rec.calls.index(["ip", "link", "del", "baivx4097"]) < rec.calls.index(
            vxlan_link_add_args(4097, "eth0", local="10.0.0.1", mtu=1450)
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
        assert vxlan_link_add_args(4097, "eth0", local="10.0.0.1", mtu=1450) in rec.calls

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

    async def test_teardown_continues_when_the_encrypted_vxlan_is_already_absent(self) -> None:
        down = link_down_args(vxlan_dev(4097))
        rec = Recorder(fail_on=lambda argv: list(argv) == down)
        plugin = _plugin(rec, vxlans=())
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()

        await plugin.teardown_session_network("s1")

        assert any(call[:4] == ["ip", "xfrm", "policy", "del"] for call in rec.calls)
        assert output_mark_del_args(4097, 4789) in rec.calls
        assert plaintext_drop_del_args(4097, 4789) in rec.calls
        assert forward_accept_del_args(4097) in rec.calls
        assert ["ip", "link", "del", vxlan_dev(4097)] in rec.calls
        assert await plugin._local_subnets.lookup("s1") is None
        assert "s1" not in plugin._sessions

    async def test_teardown_keeps_ownership_when_a_live_vxlan_cannot_be_closed(self) -> None:
        down = link_down_args(vxlan_dev(4097))
        rec = Recorder(fail_on=lambda argv: list(argv) == down)
        plugin = _plugin(rec, vxlans={vxlan_dev(4097)})
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()

        with pytest.raises(OverlayEncryptionUnavailable, match="could not be brought down"):
            await plugin.teardown_session_network("s1")

        assert not any(call[:4] == ["ip", "xfrm", "state", "del"] for call in rec.calls)
        assert "s1" in plugin._sessions
        assert await plugin._local_subnets.lookup("s1") is not None

        rec.fail_on = None
        await plugin.teardown_session_network("s1")
        assert "s1" not in plugin._sessions
        assert await plugin._local_subnets.lookup("s1") is None

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


class TestPlaintextDrop:
    """ESP protects only what this node sends. A vxlan device accepts any frame carrying its VNI,
    so without an explicit rule an encrypted session still takes injected clear text on the receive
    side -- measured on real nodes: an unregistered host injected plaintext VNI 4097 into an
    encrypted session and the member accepted it and replied in clear."""

    def test_rule_selects_the_vni_and_only_unprotected_frames(self) -> None:
        args = plaintext_drop_add_args(4097, 4789)
        # In a chain this backend owns, so a co-tenant's `-F INPUT` cannot take it and its
        # position is ours to keep (see TestOwnedChains).
        assert args[:3] == ["iptables", "-A", CHAIN_IN]
        assert args[args.index("--dport") + 1] == "4789"
        # the VNI word sits 12 bytes into the UDP header (8 UDP + 4 VXLAN flags/reserved)
        assert args[args.index("--u32") + 1] == "0>>22&0x3C@12>>8=4097"
        # ... and an ESP-decapsulated frame does not match `--pol none`, so only injected ones do
        assert args[args.index("--dir") + 1] == "in"
        assert args[args.index("--pol") + 1] == "none"
        assert args[-2:] == ["-j", "DROP"]

    def test_rule_follows_a_custom_underlay_port(self) -> None:
        args = plaintext_drop_add_args(4097, 4790)
        assert args[args.index("--dport") + 1] == "4790"

    async def test_setup_installs_it_for_an_encrypted_session(self) -> None:
        rec = _AbsentRuleRecorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        assert plaintext_drop_add_args(4097, 4789) in rec.calls
        assert output_mark_add_args(4097, 4789) in rec.calls

    def test_output_rule_marks_only_the_selected_vni(self) -> None:
        args = output_mark_add_args(4097, 4789)
        assert args[:5] == ["iptables", "-t", "mangle", "-A", CHAIN_MARK]
        assert args[args.index("--u32") + 1] == "0>>22&0x3C@12>>8=4097"
        assert args[-4:] == ["-j", "MARK", "--set-mark", f"{XFRM_MARK:#x}"]

    async def test_setup_leaves_an_unencrypted_session_alone(self) -> None:
        # Two sessions can share the underlay port with only one encrypted; dropping plaintext for
        # a VNI nobody encrypts would black-hole it.
        rec = _AbsentRuleRecorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        assert plaintext_drop_add_args(4097, 4789) not in rec.calls
        assert output_mark_add_args(4097, 4789) not in rec.calls

    async def test_setup_does_not_duplicate_when_already_present(self) -> None:
        rec = Recorder()  # a plain runner reports `iptables -C` success
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        assert plaintext_drop_check_args(4097, 4789) in rec.calls
        assert plaintext_drop_add_args(4097, 4789) not in rec.calls
        assert output_mark_check_args(4097, 4789) in rec.calls
        assert output_mark_add_args(4097, 4789) not in rec.calls

    async def test_setup_refuses_the_session_when_the_rule_cannot_be_installed(self) -> None:
        # Unlike the FORWARD accept, this one is not best-effort: without it the overlay runs
        # under a guarantee it does not have.
        class _NoU32(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                # The match module is missing, so every rule that needs it fails -- whichever
                # chain it is being added to and whichever table it is in.
                if argv[0] == "iptables" and "--u32" in argv:
                    raise RuntimeError("iptables: No chain/target/match by that name")

        rec = _NoU32()
        plugin = _plugin(rec)
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.setup_session_network(_ENC_META, _SELF)
        # and it leaves nothing half-built behind
        assert ["ip", "link", "del", vxlan_dev(4097)] in rec.calls
        assert ["ip", "link", "del", bridge_dev(4097)] in rec.calls

    async def test_teardown_removes_it(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert plaintext_drop_del_args(4097, 4789) in rec.calls
        assert output_mark_del_args(4097, 4789) in rec.calls

    async def test_adopt_reinstalls_it(self) -> None:
        # iptables is host state: a firewall reload between two agent lives leaves the devices up
        # and encrypted with the receive side open again.
        rec = _AbsentRuleRecorder()
        plugin = _plugin(rec, vxlans={vxlan_dev(4097)})
        await plugin.adopt_session_network(_ENC_META, _SELF)
        assert plaintext_drop_add_args(4097, 4789) in rec.calls
        assert link_down_args(vxlan_dev(4097)) in rec.calls
        assert link_up_args(vxlan_dev(4097)) not in rec.calls

    async def test_adopt_holds_the_tunnel_down_when_the_rule_cannot_be_restored(self) -> None:
        """A firewall reload between two agent lives reopens the receive side. Adopting and only
        logging it is the same fail-open the rule exists to close, so the vxlan device goes down:
        the containers keep running, nothing crosses the tunnel."""
        rec = _NoU32Recorder()
        plugin = _plugin(rec)
        await plugin.adopt_session_network(_ENC_META, _SELF)  # must not raise
        assert plugin._sessions["s1"] is _ENC_META  # still adopted, so it can be torn down
        assert link_down_args(vxlan_dev(4097)) in rec.calls
        # and no path to a peer is opened while it is held down. It raises rather than returning
        # quietly, so the coordinator does not record the peer as applied and stop retrying it.
        rec.calls.clear()
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.add_peer("s1", _PEER)
        assert fdb_append_args(4097, "10.0.0.2") not in rec.calls

    async def test_a_held_down_session_recovers_when_the_rule_comes_back(self) -> None:
        rec = _NoU32Recorder()
        plugin = _plugin(rec)
        await plugin.adopt_session_network(_ENC_META, _SELF)
        rec.blocked = False  # the u32/policy matches are available again
        rec.calls.clear()

        other = Member(agent_id="a3", host_ip="10.0.0.3", vtep_ip="10.0.0.3")
        await plugin.ensure_session_security("s1", [_PEER, other])
        link_up_index = rec.calls.index(link_up_args(vxlan_dev(4097)))
        expected_xfrm = [
            *_initial_xfrm_args("10.0.0.1", "10.0.0.2", _KEY),
            *_initial_xfrm_args("10.0.0.1", "10.0.0.3", _KEY),
        ]
        assert all(rec.calls.index(command) < link_up_index for command in expected_xfrm)

        await plugin.add_peer("s1", _PEER)
        assert fdb_append_args(4097, "10.0.0.2") in rec.calls

    async def test_adopt_waits_for_full_security_reconciliation_before_reopening(self) -> None:
        """A new process cannot know whether the surviving XFRM state is complete. Adoption keeps
        the tunnel down until the full published peer set has been re-asserted."""
        rec = Recorder()  # a host where the rule installs fine
        plugin = _plugin(rec)
        await plugin.adopt_session_network(_ENC_META, _SELF)
        assert link_down_args(vxlan_dev(4097)) in rec.calls
        assert link_up_args(vxlan_dev(4097)) not in rec.calls

        await plugin.ensure_session_security("s1", [_PEER])
        assert link_up_args(vxlan_dev(4097)) in rec.calls

    async def test_adopt_warns_rather_than_kills_a_running_session(self) -> None:
        class _NoU32(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                if argv and argv[0] == "iptables" and "--u32" in argv:
                    raise RuntimeError("iptables: No chain/target/match by that name")

        plugin = _plugin(_NoU32())
        await plugin.adopt_session_network(_ENC_META, _SELF)  # must not raise
        assert plugin._sessions["s1"] is _ENC_META  # still adopted


class TestSecurityDrift:
    """The reconcile that drives the backend only visits peers whose published record changed, and
    nothing that removes this state changes a record: an `iptables -F`, a firewall reload, an
    `ip xfrm state flush`. Without a pass that looks at the state itself, the first silently
    reopens the session to injected plaintext for as long as it runs."""

    async def test_reasserts_the_drop_rule(self) -> None:
        rec = _AbsentRuleRecorder()  # `iptables -C` says the rule is gone
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.ensure_session_security("s1", [])
        assert plaintext_drop_add_args(4097, 4789) in rec.calls

    async def test_reasserts_the_esp_pairs(self) -> None:
        # `_run_xfrm` replays a state add as an update, so re-running it is idempotent whether the
        # SA is still there or was flushed out from under us.
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()
        await plugin.ensure_session_security("s1", [_PEER])
        assert (
            xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY, generation=_TEST_GENERATION)[0]
            in rec.calls
        )

    async def test_raises_when_the_receive_side_cannot_be_closed(self) -> None:
        # Raising is what keeps the pass's peers out of the coordinator's applied set, so they are
        # reprogrammed once the host can protect them again.
        plugin = _plugin(_NoU32Recorder())
        await plugin.adopt_session_network(_ENC_META, _SELF)
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.ensure_session_security("s1", [])

    async def test_an_unencrypted_session_has_nothing_to_reassert(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        rec.calls.clear()
        await plugin.ensure_session_security("s1", [])
        assert rec.calls == []

    async def test_reprograms_a_peer_this_process_never_saw(self) -> None:
        """A privnet that restarted under a running session remembers none of the pairs it
        protects, and nothing refills that: the agent's reconcile does not resend a peer whose
        published record has not changed. Measured before the fix: after a restart no add_peer ever
        arrived, and teardown left this node's SAs *and policies* behind -- a leftover policy
        selects ESP for that node pair with no SA to satisfy it."""
        rec = Recorder()
        plugin = _plugin(rec)
        # adopt, not setup: the session was already running when this process started
        await plugin.adopt_session_network(_ENC_META, _SELF)
        assert plugin._encrypted_peers.get("s1") in (None, set())
        rec.calls.clear()

        await plugin.ensure_session_security("s1", [_PEER])

        assert (
            xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY, generation=_TEST_GENERATION)[0]
            in rec.calls
        )
        # and the pair is on record now, so teardown will withdraw it
        assert plugin._encrypted_peers["s1"] == {"10.0.0.2"}

    async def test_a_failed_reassert_closes_the_tunnel(self) -> None:
        """This is a re-assert, not a first program: the FDB entry for that peer is already open,
        so a failure is not "the peer is unreachable" but "the peer is reachable and may be
        unprotected". Logging past it leaves the session sending in clear."""
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.fail_on = lambda argv: argv[:2] == ["ip", "xfrm"]
        rec.calls.clear()

        with pytest.raises(RuntimeError):
            await plugin.ensure_session_security("s1", [_PEER])

        assert link_down_args(vxlan_dev(4097)) in rec.calls
        # and the pair is no longer trusted, so a new endpoint is not given an FDB entry on it
        assert not plugin._pair_is_protected(_ENC_META, "s1", "10.0.0.2")

    async def test_a_failed_reopen_keeps_the_session_closed(self) -> None:
        """Clearing the held-down mark before the device is actually up loses the one record that
        says the session is still closed, so no later pass has a reason to try again."""

        class _LinkUpFails(_AbsentRuleRecorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                if list(argv) == link_up_args(vxlan_dev(4097)):
                    self.calls.append(list(argv))
                    raise RuntimeError("RTNETLINK answers: Operation not permitted")
                await super().__call__(argv)

        plugin = _plugin(_NoU32Recorder())
        await plugin.adopt_session_network(_ENC_META, _SELF)
        assert plugin.security_state("s1") is VxlanSecurityState.BLOCKED

        plugin._runner = _LinkUpFails()  # protection returns, but the device will not come up
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.ensure_session_security("s1", [])
        assert plugin.security_state("s1") is VxlanSecurityState.BLOCKED

    async def test_a_failed_link_down_is_not_recorded_as_blocked_and_is_retried(self) -> None:
        """BLOCKED means the kernel confirmed link-down, not merely that it was requested."""

        class _LinkDownFails(Recorder):
            fail_down = True

            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                if self.fail_down and list(argv) == link_down_args(vxlan_dev(4097)):
                    raise RuntimeError("RTNETLINK answers: Operation not permitted")

        rec = _LinkDownFails()
        plugin = _plugin(rec, vxlans={vxlan_dev(4097)})
        await plugin.adopt_session_network(_ENC_META, _SELF)
        assert plugin.security_state("s1") is VxlanSecurityState.BLOCKING

        rec.calls.clear()
        with pytest.raises(OverlayEncryptionUnavailable, match="could not be brought down"):
            await plugin.ensure_session_security("s1", [_PEER])
        assert rec.calls == [link_down_args(vxlan_dev(4097))]
        assert plugin.security_state("s1") is VxlanSecurityState.BLOCKING

        rec.fail_down = False
        rec.calls.clear()
        await plugin.ensure_session_security("s1", [_PEER])
        down_index = rec.calls.index(link_down_args(vxlan_dev(4097)))
        xfrm_index = rec.calls.index(
            xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY, generation=_TEST_GENERATION)[0]
        )
        up_index = rec.calls.index(link_up_args(vxlan_dev(4097)))
        assert down_index < xfrm_index < up_index
        assert plugin.security_state("s1") is VxlanSecurityState.READY

    async def test_an_unknown_session_is_a_noop(self) -> None:
        rec = Recorder()
        await _plugin(rec).ensure_session_security("nope", [])
        assert rec.calls == []


class TestSecurityStateMachine:
    class _StateRecorder(Recorder):
        plugin: VxlanNetworkPlugin | None
        states: list[VxlanSecurityState | None]

        def __init__(self) -> None:
            super().__init__()
            self.plugin = None
            self.states = []

        @override
        async def __call__(self, argv: Sequence[str]) -> None:
            if self.plugin is not None and list(argv[:2]) == ["ip", "xfrm"]:
                self.states.append(self.plugin.security_state("s1"))
            await super().__call__(argv)

    async def test_setup_selects_ready_or_plaintext(self) -> None:
        encrypted = _plugin(Recorder())
        await encrypted.setup_session_network(_ENC_META, _SELF)
        assert encrypted.security_state("s1") is VxlanSecurityState.READY

        plaintext = _plugin(Recorder())
        await plaintext.setup_session_network(_META, _SELF)
        assert plaintext.security_state("s1") is VxlanSecurityState.PLAINTEXT

    async def test_adopted_session_restores_while_blocked(self) -> None:
        rec = self._StateRecorder()
        plugin = _plugin(rec)
        rec.plugin = plugin

        await plugin.adopt_session_network(_ENC_META, _SELF)
        assert plugin.security_state("s1") is VxlanSecurityState.BLOCKED

        await plugin.ensure_session_security("s1", [_PEER])
        assert VxlanSecurityState.RESTORING in rec.states
        assert plugin.security_state("s1") is VxlanSecurityState.READY

    async def test_ready_session_verifies_without_closing_the_tunnel(self) -> None:
        rec = self._StateRecorder()
        plugin = _plugin(rec)
        rec.plugin = plugin
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()
        rec.states.clear()

        await plugin.ensure_session_security("s1", [_PEER])

        assert VxlanSecurityState.VERIFYING in rec.states
        assert link_down_args(vxlan_dev(4097)) not in rec.calls
        assert plugin.security_state("s1") is VxlanSecurityState.READY

    async def test_failed_verification_transitions_to_blocked(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.fail_on = lambda argv: argv[:2] == ["ip", "xfrm"]

        with pytest.raises(RuntimeError):
            await plugin.ensure_session_security("s1", [_PEER])

        assert plugin.security_state("s1") is VxlanSecurityState.BLOCKED

    async def test_teardown_removes_the_machine(self) -> None:
        plugin = _plugin(Recorder())
        await plugin.setup_session_network(_ENC_META, _SELF)

        await plugin.teardown_session_network("s1")

        assert plugin.security_state("s1") is None

    def test_blocked_state_requires_a_restore_pass_before_ready(self) -> None:
        machine = VxlanSecurityStateMachine(VxlanSecurityState.BLOCKED)

        assert machine.transition(VxlanSecurityEvent.PROTECTION_READY) is VxlanSecurityState.BLOCKED
        assert (
            machine.transition(VxlanSecurityEvent.RECONCILE_STARTED) is VxlanSecurityState.RESTORING
        )
        assert machine.transition(VxlanSecurityEvent.PROTECTION_READY) is VxlanSecurityState.READY

    @pytest.mark.parametrize(
        ("initial", "expected"),
        [
            (VxlanSecurityState.READY, VxlanSecurityState.BLOCKING),
            (VxlanSecurityState.VERIFYING, VxlanSecurityState.BLOCKING),
            (VxlanSecurityState.RESTORING, VxlanSecurityState.BLOCKED),
        ],
    )
    def test_protection_failure_blocks_encrypted_states(
        self,
        initial: VxlanSecurityState,
        expected: VxlanSecurityState,
    ) -> None:
        machine = VxlanSecurityStateMachine(initial)

        assert (
            machine.transition(VxlanSecurityEvent.PROTECTION_FAILED, reason="lost protection")
            is expected
        )
        assert machine.failure_reason == "lost protection"

    def test_blocking_becomes_blocked_only_after_link_down_confirmation(self) -> None:
        machine = VxlanSecurityStateMachine(VxlanSecurityState.READY)

        assert (
            machine.transition(VxlanSecurityEvent.PROTECTION_FAILED) is VxlanSecurityState.BLOCKING
        )
        assert (
            machine.transition(VxlanSecurityEvent.RECONCILE_STARTED) is VxlanSecurityState.BLOCKING
        )
        assert machine.transition(VxlanSecurityEvent.TUNNEL_BLOCKED) is VxlanSecurityState.BLOCKED


class TestDeviceInventory:
    """Both callers ask one question -- does this device still exist -- and the `ip -d` attribute
    dump that would answer more is the part that breaks. Measured on three nodes running the same
    iproute2 6.1.0 on Ubuntu 24.04: `ip -d -j link show type vxlan` is valid JSON on kernel 6.8,
    malformed on 6.14 (`"id":60001fan-map ,"link":...`), and empty on 6.17."""

    def test_the_inventory_command_asks_for_no_details(self) -> None:
        # `-d` is what differs across kernels; nothing here needs what it adds.
        source = inspect.getsource(vx._list_vxlan_devices)
        assert '"-d"' not in source

    @pytest.mark.parametrize(
        "line, expected",
        [
            ("12: baivx4097: <BROADCAST,MULTICAST,UP> mtu 1412 qdisc noqueue", "baivx4097"),
            ("3: eth0@if4: <BROADCAST> mtu 1500", "eth0"),
            ("7:    flannel.1: <BROADCAST> mtu 1450", "flannel.1"),
        ],
    )
    def test_a_link_line_yields_its_name(self, line: str, expected: str) -> None:
        match = vx._VXLAN_LINE.match(line)
        assert match is not None and match.group("name") == expected

    @pytest.mark.parametrize("line", ["", "Cannot find device", "  ", "not-a-link-line"])
    def test_a_line_that_is_not_a_link_is_skipped(self, line: str) -> None:
        assert vx._VXLAN_LINE.match(line) is None


class TestExclusiveOverlayPort:
    """The VNI-scoped OUTPUT mark keeps other VXLAN devices out of this policy."""

    async def test_an_encrypted_session_allows_a_shared_port(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec, vxlans={"flannel.1"})
        await plugin.setup_session_network(_ENC_META, _SELF)
        assert vxlan_link_add_args(4097, "eth0", local="10.0.0.1", mtu=1412) in rec.calls

    async def test_our_own_devices_are_not_a_collision(self) -> None:
        # Every session on this node shares the port with its siblings by design.
        rec = Recorder()
        plugin = _plugin(rec, vxlans={vxlan_dev(4096), vxlan_dev(4097)})
        await plugin.setup_session_network(_ENC_META, _SELF)  # must not raise

    async def test_a_neighbour_on_another_port_is_fine(self) -> None:
        # The port is what separates them, and this one is separated.
        rec = Recorder()
        plugin = _plugin(rec, vxlans={"flannel.1"})
        await plugin.setup_session_network(_ENC_META, _SELF)  # must not raise

    async def test_an_unencrypted_session_is_unaffected(self) -> None:
        # Without a policy there is nothing to sweep the neighbour into.
        rec = Recorder()
        plugin = _plugin(rec, vxlans={"flannel.1"})
        await plugin.setup_session_network(_META, _SELF)  # must not raise

    async def test_a_custom_port_can_also_be_shared(self) -> None:
        meta = SessionNetMeta(
            session_id="s1",
            subnet="10.128.5.0/24",
            backend=NetworkBackendKind.VXLAN,
            mtu=1412,
            vni=4097,
            encryption_key=_KEY,
            vxlan_port=4790,
        )
        rec = Recorder()
        await _plugin(rec, vxlans={"flannel.1"}).setup_session_network(meta, _SELF)
        await _plugin(rec, vxlans={"other.vx"}).setup_session_network(meta, _SELF)

    async def test_a_host_that_cannot_be_inspected_is_not_refused(self) -> None:
        # The check catches a specific, detectable collision; it is not a reason to refuse every
        # host whose `ip` cannot report vxlan attributes.
        async def broken() -> dict[str, int]:
            raise RuntimeError("ip: command not found")

        plugin = _plugin(Recorder())
        plugin._vxlan_lister = broken
        await plugin.setup_session_network(_ENC_META, _SELF)  # must not raise


class TestSharedPairRaces:
    """The SA and policy are shared by every session between the same two nodes on the same port,
    so the refcount decision and the commands that follow from it are one step. Without a per-pair
    lock they interleave into "A decides it is the last user, B programs the pair, A deletes what B
    just made" -- and B is left with an open FDB and nothing encrypting it."""

    async def test_a_teardown_cannot_delete_a_pair_another_session_just_programmed(self) -> None:
        # A slow runner widens the window the lock has to cover: without it, B's program lands
        # between A's refcount decision and A's deletes.
        class _Slow(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                if argv[:2] == ["ip", "xfrm"]:
                    await asyncio.sleep(0)

        rec = _Slow()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        other = SessionNetMeta(
            session_id="s2",
            subnet="10.128.6.0/24",
            backend=NetworkBackendKind.VXLAN,
            mtu=1412,
            vni=4098,
            encryption_key=_KEY,
        )
        await plugin.setup_session_network(other, _SELF)
        await plugin.add_peer("s1", _PEER)  # s1 programs the pair

        await asyncio.gather(
            plugin.del_peer("s1", _PEER),  # s1 leaves: it is the last user of the pair
            plugin.add_peer("s2", _PEER),  # s2 arrives on the very same pair
        )

        # Whatever the order, the surviving session must not be left with an open path and no
        # encryption: either the pair is still programmed, or s2 never opened its FDB.
        key = ("10.0.0.1", "10.0.0.2", 4789)
        if fdb_append_args(4098, "10.0.0.2") in rec.calls:
            assert key in plugin._programmed_pairs
        assert plugin._pair_users.get(key, set()) in (set(), {"s2"})


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
        out = xfrm_add_args("10.0.0.1", "10.0.0.2", _KEY)
        # state[0] is the out SA src=self dst=peer; extract its spi
        state_out = out[0]
        spi_ab = state_out[state_out.index("spi") + 1]
        rev = xfrm_add_args("10.0.0.2", "10.0.0.1", _KEY)
        # rev's in-SA is state[1]: src=self(=.1) dst=peer... from .2's perspective the in SA is
        # src=.1 dst=.2 — same directed pair as A's out SA, so same SPI.
        state_in_from_b = rev[1]
        spi_from_b = state_in_from_b[state_in_from_b.index("spi") + 1]
        assert spi_ab == spi_from_b

    def test_aead_key_is_a_derived_key_plus_a_derived_salt(self) -> None:
        # rfc4106 needs key(32B)+salt(4B). Both are derived: the key from the cluster secret for
        # this node pair, the salt from that key and the SPI.
        out = xfrm_add_args("10.0.0.1", "10.0.0.2", _KEY)
        aead_key = out[0][out[0].index("aead") + 2]
        assert len(aead_key) == len("0x") + 64 + 8  # 32B key + 4B salt, hex
        assert aead_key.startswith("0x" + _pair_key(_KEY, "10.0.0.1", "10.0.0.2"))

    def test_add_builds_two_states_and_one_outbound_policy(self) -> None:
        out = xfrm_add_args("10.0.0.1", "10.0.0.2", _KEY)
        kinds = [(a[1], a[2]) for a in out]  # ("xfrm", "state"|"policy")
        assert kinds == [
            ("xfrm", "state"),
            ("xfrm", "state"),
            ("xfrm", "policy"),
        ]
        policy = out[2]
        assert "dport" in policy and "4789" in policy
        assert policy[policy.index("dir") + 1] == "out"
        assert policy[policy.index("mark") + 1 : policy.index("mark") + 4] == [
            f"{XFRM_MARK:#x}",
            "mask",
            "0xffffffff",
        ]
        assert policy[policy.index("reqid") + 1] == f"{XFRM_REQID:#x}"
        assert all(state[state.index("reqid") + 1] == f"{XFRM_REQID:#x}" for state in out[:2])

    def test_xfrm_ownership_is_distinct_from_docker(self) -> None:
        docker_mark_and_reqid = 0xD0C4E3

        assert docker_mark_and_reqid != XFRM_MARK
        assert docker_mark_and_reqid != XFRM_REQID
        assert len({XFRM_MARK, XFRM_REQID}) == 2

    def test_del_matches_add_spis(self) -> None:
        add = xfrm_add_args("10.0.0.1", "10.0.0.2", _KEY)
        dele = xfrm_del_args("10.0.0.1", "10.0.0.2")
        add_out_spi = add[0][add[0].index("spi") + 1]
        del_out_spi = dele[0][dele[0].index("spi") + 1]
        assert add_out_spi == del_out_spi

    def test_three_generation_slots_reuse_spi_but_never_key(self) -> None:
        current = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY, generation=_TEST_GENERATION)[0]
        adjacent = xfrm_state_add_args(
            "10.0.0.1", "10.0.0.2", _KEY, generation=_TEST_GENERATION + 1
        )[0]
        reused_slot = xfrm_state_add_args(
            "10.0.0.1", "10.0.0.2", _KEY, generation=_TEST_GENERATION + 3
        )[0]

        def value(command: list[str], name: str, offset: int = 1) -> str:
            return command[command.index(name) + offset]

        assert value(current, "spi") != value(adjacent, "spi")
        assert value(current, "spi") == value(reused_slot, "spi")
        assert value(current, "aead", 2) != value(reused_slot, "aead", 2)


class TestKeyRotation:
    async def test_clock_rollback_does_not_reactivate_a_retired_generation(self) -> None:
        generation = _TEST_GENERATION

        def current_generation() -> int:
            return generation

        rec = Recorder()
        plugin = _plugin(rec, key_generation=current_generation)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()

        generation -= 1
        await plugin.ensure_session_security("s1", [_PEER])

        policies = _policies(rec)
        assert len(policies) == 1
        assert policies[0][policies[0].index("spi") + 1] == (
            f"{vx._esp_spi('10.0.0.1', '10.0.0.2', _TEST_GENERATION):#x}"
        )
        assert plugin._pair_active_generations[("10.0.0.1", "10.0.0.2", 4789)] == (_TEST_GENERATION)

    async def test_rotation_installs_next_generation_before_switching_policy(self) -> None:
        generation = _TEST_GENERATION

        def current_generation() -> int:
            return generation

        rec = Recorder()
        plugin = _plugin(rec, key_generation=current_generation)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()

        generation += 1
        await plugin.ensure_session_security("s1", [_PEER])

        new_future = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY, generation=generation + 1)
        new_policy = xfrm_policy_add_args("10.0.0.1", "10.0.0.2", generation=generation)[0]
        policy_index = rec.calls.index(new_policy)
        assert all(rec.calls.index(command) < policy_index for command in new_future)
        assert plugin._pair_slot_generations[("10.0.0.1", "10.0.0.2", 4789)] == {
            (generation - 1) % 3: generation - 1,
            generation % 3: generation,
            (generation + 1) % 3: generation + 1,
        }

    async def test_rotation_recreates_only_the_expired_spi_slot(self) -> None:
        generation = _TEST_GENERATION

        def current_generation() -> int:
            return generation

        rec = Recorder()
        plugin = _plugin(rec, key_generation=current_generation)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()

        generation += 1
        await plugin.ensure_session_security("s1", [_PEER])

        deletes = [command for command in _states(rec) if command[3] == "del"]
        assert deletes == xfrm_state_del_args("10.0.0.1", "10.0.0.2", generation=generation + 1)

    async def test_pair_uses_previous_current_and_next_generations(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.add_peer("s1", _PEER)

        added_spis = {
            command[command.index("spi") + 1] for command in _states(rec) if command[3] == "add"
        }
        assert len(added_spis) == 6
        policy = _policies(rec)[0]
        assert policy[policy.index("spi") + 1] == (
            f"{vx._esp_spi('10.0.0.1', '10.0.0.2', _TEST_GENERATION):#x}"
        )


class TestAeadSalt:
    """RFC 4106's nonce is salt || per-packet IV, so two SAs sharing a (key, salt) pair are one
    repeated IV away from a repeated nonce. Linux happens to give each SA a random IV base, but
    that is the kernel's choice; what is programmed here should not depend on it."""

    def _salt_of(self, argv: list[str]) -> str:
        return argv[argv.index("aead") + 2][-8:]

    def test_the_two_directions_get_different_salts(self) -> None:
        out, inn = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)
        assert self._salt_of(out) != self._salt_of(inn)

    def test_different_peers_get_different_salts(self) -> None:
        a = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)[0]
        b = xfrm_state_add_args("10.0.0.1", "10.0.0.3", _KEY)[0]
        assert self._salt_of(a) != self._salt_of(b)

    def test_both_ends_compute_the_same_salt_for_one_sa(self) -> None:
        # A's out-SA and B's in-SA are the same SA; they must agree without a handshake.
        a_out = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)[0]
        b_in = xfrm_state_add_args("10.0.0.2", "10.0.0.1", _KEY)[1]
        assert self._salt_of(a_out) == self._salt_of(b_in)

    def test_both_directions_of_a_pair_share_the_key(self) -> None:
        # Only the salt is per-SA: the key is what lets one policy select either SA of the pair.
        out, inn = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)
        keys = {argv[argv.index("aead") + 2][:-8] for argv in (out, inn)}
        assert len(keys) == 1


class TestPerPairKey:
    """`ip xfrm state` prints an SA's key back in the clear, so whatever goes into the kernel is
    readable by anything that can run it on that node. What went in before was the cluster secret
    itself, on every SA of every node."""

    def _key_of(self, argv: list[str]) -> str:
        return argv[argv.index("aead") + 2][2:-8]  # strip "0x" and the 4-byte salt

    def test_the_cluster_secret_does_not_reach_the_kernel(self) -> None:
        for argv in xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY):
            assert _KEY not in argv[argv.index("aead") + 2]

    def test_different_pairs_get_different_keys(self) -> None:
        a = self._key_of(xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)[0])
        b = self._key_of(xfrm_state_add_args("10.0.0.1", "10.0.0.3", _KEY)[0])
        assert a != b

    def test_both_ends_of_a_pair_derive_the_same_key(self) -> None:
        # A computes it as (self=A, peer=B); B as (self=B, peer=A). No handshake, same value.
        a = self._key_of(xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)[0])
        b = self._key_of(xfrm_state_add_args("10.0.0.2", "10.0.0.1", _KEY)[1])
        assert a == b

    def test_the_key_keeps_the_size_rfc4106_expects(self) -> None:
        assert len(bytes.fromhex(_pair_key(_KEY, "10.0.0.1", "10.0.0.2"))) == 32

    def test_a_different_cluster_secret_gives_a_different_pair_key(self) -> None:
        other = "ff" * 32
        assert _pair_key(_KEY, "10.0.0.1", "10.0.0.2") != _pair_key(other, "10.0.0.1", "10.0.0.2")


class TestEncryptedPeers:
    async def test_add_peer_programs_xfrm_before_fdb_when_encrypted(self) -> None:
        # The FDB entry is what makes a frame leave for that peer. Appending it first opens a
        # window in which an encrypted session sends clear text — and if the xfrm commands then
        # fail, the coordinator logs it and carries on, so the window never closes.
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.add_peer("s1", _PEER)
        # iptables aside: add_peer also re-checks the plaintext-drop rule, which is not what the
        # ordering here is about.
        assert [c for c in rec.calls if c[0] != "iptables"] == [
            *_initial_xfrm_args("10.0.0.1", "10.0.0.2", _KEY),
            fdb_append_args(4097, "10.0.0.2"),
        ]

    async def test_a_failed_xfrm_leaves_no_path_for_clear_text(self) -> None:
        """Fail-closed: the peer stays unreachable rather than reachable and unprotected."""
        rec = Recorder(fail_on=lambda argv: argv[:2] == ["ip", "xfrm"])
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        with pytest.raises(RuntimeError):
            await plugin.add_peer("s1", _PEER)
        assert fdb_append_args(4097, "10.0.0.2") not in rec.calls

    async def test_a_failed_xfrm_is_retried_not_skipped(self) -> None:
        """The pair must not be remembered as programmed when the commands did not land.

        Recording it would make every later reconcile take the `already programmed` shortcut, and
        the session would run unencrypted for good with nothing left to retry.
        """
        rec = Recorder(fail_on=lambda argv: argv[:2] == ["ip", "xfrm"])
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        with pytest.raises(RuntimeError):
            await plugin.add_peer("s1", _PEER)

        rec.fail_on = None
        rec.calls.clear()
        await plugin.add_peer("s1", _PEER)
        assert [c for c in rec.calls if c[0] != "iptables"] == [
            *_initial_xfrm_args("10.0.0.1", "10.0.0.2", _KEY),
            fdb_append_args(4097, "10.0.0.2"),
        ]

    async def test_a_node_with_no_vtep_does_not_open_the_tunnel(self) -> None:
        """The adopt path: setup refuses an encrypted session on a VTEP-less node, but an agent
        restarting under a running one cannot. Without a VTEP there is no `src` to anchor the SAs
        on, so the peer must stay unreachable rather than reachable in clear text."""
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.adopt_session_network(
            _ENC_META, Member(agent_id="a1", host_ip="10.0.0.1", vtep_ip=None)
        )
        rec.calls.clear()
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.ensure_session_security("s1", [_PEER])
        assert link_up_args(vxlan_dev(4097)) not in rec.calls

        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.add_peer("s1", _PEER)
        assert fdb_append_args(4097, "10.0.0.2") not in rec.calls
        assert not any(c[:2] == ["ip", "xfrm"] for c in rec.calls)

    async def test_add_peer_no_xfrm_without_key(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)  # plaintext meta
        rec.calls.clear()
        await plugin.add_peer("s1", _PEER)
        assert rec.calls == [fdb_append_args(4097, "10.0.0.2")]

    async def test_del_peer_withdraws_fdb_before_xfrm(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()
        await plugin.del_peer("s1", _PEER)
        assert rec.calls == [
            fdb_del_args(4097, "10.0.0.2"),
            *xfrm_del_args("10.0.0.1", "10.0.0.2"),
        ]

    async def test_a_failed_fdb_withdrawal_keeps_xfrm(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.fail_on = lambda argv: list(argv) == fdb_del_args(4097, "10.0.0.2")
        rec.calls.clear()

        with pytest.raises(RuntimeError):
            await plugin.del_peer("s1", _PEER)

        assert rec.calls == [fdb_del_args(4097, "10.0.0.2")]
        assert ("10.0.0.1", "10.0.0.2", 4789) in plugin._programmed_pairs

    async def test_del_peer_refuses_while_unicast_fdb_remains(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        await plugin.add_endpoint(
            "s1", ip="10.128.5.7", mac="02:42:0a:80:05:07", vtep_ip="10.0.0.2"
        )
        rec.calls.clear()

        with pytest.raises(OverlayEncryptionUnavailable, match="FDB entries still exist"):
            await plugin.del_peer("s1", _PEER)

        assert rec.calls == []

    async def test_endpoint_fdb_failure_is_not_hidden(self) -> None:
        endpoint_fdb = fdb_del_args(4097, "10.0.0.2", mac="02:42:0a:80:05:07")
        rec = Recorder(fail_on=lambda argv: list(argv) == endpoint_fdb)
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)

        with pytest.raises(RuntimeError):
            await plugin.del_endpoint(
                "s1", ip="10.128.5.7", mac="02:42:0a:80:05:07", vtep_ip="10.0.0.2"
            )

        assert neigh_del_args(4097, "10.128.5.7") not in rec.calls

    async def test_a_pair_this_process_did_not_program_is_left_alone(self) -> None:
        """Only the privnet restarted: the agent still remembers its peers as applied and never
        re-sends them, so the refcount here rebuilds empty while other sessions are still carried
        by that SA and policy. Removing it on an empty count drops them to clear text."""
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.del_peer("s1", _PEER)  # no add_peer in this process
        assert not any(c[:2] == ["ip", "xfrm"] for c in rec.calls)
        assert fdb_del_args(4097, "10.0.0.2") in rec.calls


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
        assert [c for c in rec.calls if c[0] != "iptables"] == [
            fdb_replace_args(4097, "02:42:0a:80:05:07", "10.0.0.2"),
            neigh_replace_args(4097, "10.128.5.7", "02:42:0a:80:05:07"),
        ]

    async def test_endpoint_is_refused_when_the_peer_pair_is_unprotected(self) -> None:
        """The membership reconcile runs whether or not add_peer succeeded, and a unicast FDB
        entry opens a route to that VTEP on its own -- withholding only the broadcast entry leaves
        the peer reachable in clear text the moment its endpoint is published."""
        rec = Recorder(fail_on=lambda argv: argv[:2] == ["ip", "xfrm"])
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        with pytest.raises(RuntimeError):
            await plugin.add_peer("s1", _PEER)  # the SAs do not land
        rec.calls.clear()

        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.add_endpoint(
                "s1", ip="10.128.5.7", mac="02:42:0a:80:05:07", vtep_ip="10.0.0.2"
            )
        assert fdb_replace_args(4097, "02:42:0a:80:05:07", "10.0.0.2") not in rec.calls
        assert neigh_replace_args(4097, "10.128.5.7", "02:42:0a:80:05:07") not in rec.calls

    async def test_endpoint_is_programmed_once_the_pair_is_protected(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()
        await plugin.add_endpoint(
            "s1", ip="10.128.5.7", mac="02:42:0a:80:05:07", vtep_ip="10.0.0.2"
        )
        assert fdb_replace_args(4097, "02:42:0a:80:05:07", "10.0.0.2") in rec.calls

    async def test_an_unencrypted_endpoint_is_unaffected(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)  # plaintext meta
        rec.calls.clear()
        await plugin.add_endpoint(
            "s1", ip="10.128.5.7", mac="02:42:0a:80:05:07", vtep_ip="10.0.0.2"
        )
        assert fdb_replace_args(4097, "02:42:0a:80:05:07", "10.0.0.2") in rec.calls

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
        # The outbound policy selects on the VXLAN UDP port; a selector left on 4789 while the
        # device moved would leave the tunnel unencrypted rather than fail loudly.
        policies = [
            a for a in xfrm_add_args("1.1.1.1", "2.2.2.2", "ab" * 32, dstport=4790) if "policy" in a
        ]
        assert len(policies) == 1
        for args in policies:
            assert args[args.index("dport") + 1] == "4790"
        for args in xfrm_del_args("1.1.1.1", "2.2.2.2", dstport=4790):
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
        # And the failure outlives the log line: the session is left RUNNING on purpose, so
        # without this the only trace is in the agent's log while the user sees a rendezvous
        # that never completes.
        assert plugin.unreachable_peers("s1") == frozenset({"10.0.0.2"})

    async def test_one_probe_per_peer_not_per_kernel(self) -> None:
        # Every kernel behind a peer rides the same tunnel, so asking once per kernel multiplies
        # tasks and raw sockets by that peer's kernel count for an answer that cannot differ.
        reach = _ReachRecorder(True)
        plugin = _plugin(Recorder(), reach=reach)
        await plugin.setup_session_network(_META, _SELF)
        for last in range(9, 13):
            await plugin.add_endpoint(
                "s1", ip=f"10.128.5.{last}", mac=f"02:42:0a:80:05:{last:02x}", vtep_ip="10.0.0.2"
            )
        await self._drain(plugin, "s1")
        assert len(reach.calls) == 1

    async def test_distinct_peers_are_each_probed(self) -> None:
        reach = _ReachRecorder(True)
        plugin = _plugin(Recorder(), reach=reach)
        await plugin.setup_session_network(_META, _SELF)
        for host, peer in ((9, "10.0.0.2"), (10, "10.0.0.3")):
            await plugin.add_endpoint(
                "s1", ip=f"10.128.5.{host}", mac=f"02:42:0a:80:05:{host:02x}", vtep_ip=peer
            )
        await self._drain(plugin, "s1")
        assert len(reach.calls) == 2

    async def test_a_peer_that_did_not_answer_is_asked_again(self, monkeypatch: Any) -> None:
        # The first endpoint behind a peer may simply have been early -- its container still
        # starting. A peer written off on that is a peer nothing ever asks about again.
        monkeypatch.setattr(vx, "_REACH_RETRY_DELAY_SEC", 0)
        reach = _ReachRecorder(False)
        plugin = _plugin(Recorder(), reach=reach)
        await plugin.setup_session_network(_META, _SELF)
        await plugin.add_endpoint(
            "s1", ip="10.128.5.9", mac="02:42:0a:80:05:09", vtep_ip="10.0.0.2"
        )
        await self._drain(plugin, "s1")
        first = len(reach.calls)

        reach.answer = True
        await plugin.add_endpoint(
            "s1", ip="10.128.5.10", mac="02:42:0a:80:05:0a", vtep_ip="10.0.0.2"
        )
        await self._drain(plugin, "s1")
        assert len(reach.calls) > first
        assert plugin.unreachable_peers("s1") == frozenset()

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
        cmds = xfrm_add_args("10.0.0.1", "10.0.0.2", "ab" * 32)
        states = [c for c in cmds if c[:3] == ["ip", "xfrm", "state"]]
        assert len(states) == 2
        for c in states:
            assert c[3] == "add", c

    def test_policies_stay_update(self) -> None:
        # XFRM_MSG_UPDPOLICY does create when absent, so the policies need no add/EEXIST dance.
        cmds = xfrm_add_args("10.0.0.1", "10.0.0.2", "ab" * 32)
        policies = [c for c in cmds if c[:3] == ["ip", "xfrm", "policy"]]
        assert len(policies) == 1
        for c in policies:
            assert c[3] == "update", c

    async def test_existing_sa_is_replayed_as_update(self) -> None:
        # Same-generation verification re-asserts states that already exist; `add` is EEXIST and
        # may fall back to update because the AEAD key has not changed.
        class FailAdd(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                if list(argv[:4]) == ["ip", "xfrm", "state", "add"]:
                    raise RuntimeError("RTNETLINK answers: File exists")

        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec = FailAdd()
        plugin._runner = rec
        await plugin.ensure_session_security("s1", [_PEER])
        verbs = [c[3] for c in rec.calls if c[:3] == ["ip", "xfrm", "state"]]
        assert verbs.count("add") == 6 and verbs.count("update") == 6, verbs

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

    Measured before pair refcounting: after a session, one node still held `SAD 2 / SPD 1` pointing
    at a dead peer pod IP while the other was clean. A stale outbound policy can select ESP after
    its SA is gone and black-hole later plaintext VXLAN traffic on the same node pair and port.
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

    async def test_restarted_backend_deletes_journalled_peer_state(self) -> None:
        """The kernel outlives the privileged executor, but its in-memory session registry does
        not. Recovery must restore ownership before teardown or the real backend returns early."""
        rec = Recorder()
        first = _plugin(rec)
        await first.setup_session_network(_ENC_META, _SELF)
        await first.add_peer("s1", _PEER)

        restarted = _plugin(rec)
        await restarted.adopt_session_network(_ENC_META, _SELF)
        await restarted.restore_session_peer_ownership("s1", [_PEER])
        rec.calls.clear()

        await restarted.teardown_session_network("s1")

        deletes = [c for c in self._xfrm(rec) if c[3] in ("delete", "del")]
        assert deletes
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


class TestTheNodePairIsProgrammedOnce:
    """ESP state and policy both belong to the node pair, not to a session.

    The policy has no choice about it: its selector is the OUTER packet — VTEP addresses and the
    VXLAN UDP port — and the VNI that names a session lives inside that packet's payload, where no
    XFRM selector reaches. The SA follows, because the key is the cluster's (see the manager's
    `overlay_encryption_key`): every session between two nodes wants the same SA with the same
    secret. What used to happen instead was measurable and bad — of two SAs matching one policy the
    kernel carried every packet on one and none on the other, and whichever session ended first
    deleted the policy and dropped the survivors to clear text.
    """

    async def _two_sessions(self, rec: Recorder) -> VxlanNetworkPlugin:
        plugin = _plugin(rec)
        for session_id, vni in (("s1", 4097), ("s2", 4098)):
            meta = _enc_meta(session_id, vni)
            await plugin.setup_session_network(meta, _SELF)
            await plugin.add_peer(session_id, _PEER)
        return plugin

    async def test_the_second_session_programs_nothing(self) -> None:
        rec = Recorder()
        await self._two_sessions(rec)

        assert len([c for c in _states(rec) if c[3] == "add"]) == 6, (
            "one three-generation SA ring for the node pair, not one per session"
        )
        assert len(_policies(rec)) == 1

    async def test_the_first_teardown_leaves_it_for_the_other(self) -> None:
        rec = Recorder()
        plugin = await self._two_sessions(rec)
        rec.calls.clear()

        await plugin.teardown_session_network("s1")

        assert _states(rec) == [], "the surviving session is still carried by this SA"
        assert _policies(rec) == []

    async def test_the_last_teardown_removes_it(self) -> None:
        rec = Recorder()
        plugin = await self._two_sessions(rec)
        await plugin.teardown_session_network("s1")
        rec.calls.clear()

        await plugin.teardown_session_network("s2")

        assert [c[3] for c in _policies(rec)] == ["del"]
        assert [c[3] for c in _states(rec)] == ["del"] * 6

    async def test_a_lone_session_still_removes_it(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()

        await plugin.teardown_session_network("s1")

        assert [c[3] for c in _policies(rec)] == ["del"]
        assert [c[3] for c in _states(rec)] == ["del"] * 6

    async def test_a_different_peer_is_a_different_pair(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        await plugin.add_peer("s1", Member(agent_id="a3", host_ip="10.0.0.3", vtep_ip="10.0.0.3"))

        assert len(_policies(rec)) == 2
        assert len([c for c in _states(rec) if c[3] == "add"]) == 12

    def test_a_different_peer_gets_a_different_spi(self) -> None:
        """The SPI names the PAIR. Deriving it from the local end alone would still satisfy both
        properties the builder tests check — it stays directional, and both ends still agree —
        because SAs are keyed by (dst, spi, proto) and the dst already differs. It would just make
        every tunnel out of this node wear the same number, which is a needless way to make
        `ip xfrm state` unreadable when something is wrong.
        """

        def spi(cmd: list[str]) -> str:
            return cmd[cmd.index("spi") + 1]

        to_b = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)[0]
        to_c = xfrm_state_add_args("10.0.0.1", "10.0.0.3", _KEY)[0]

        assert spi(to_b) != spi(to_c)

    async def test_the_spi_does_not_depend_on_the_session(self) -> None:
        """Two sessions between the same nodes derive the same SA, which is the point: there is
        nothing to tell apart, so nothing for the policy to pick wrongly."""
        a = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)
        b = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)

        assert a == b


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

        assert len([c for c in _states(rec) if c[3] == "add"]) == 6, (
            "the three-generation SA ring did get installed"
        )
        assert plugin._encrypted_peers.get("s1") == {"10.0.0.2"}, (
            "teardown must still know to unprogram what did get installed"
        )


class TestAntiReplay:
    """A fresh SA has no replay window and a 32-bit sequence. The window means a captured ESP
    packet is accepted again; the sequence means a busy tunnel STOPS -- a non-ESN SA does not wrap,
    it errors. At 100k packet/s that ceiling arrives in ~11.9 hours, inside the rotation interval,
    and GSO spends one number per segment."""

    def test_the_sa_carries_a_replay_window(self) -> None:
        out, inn = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)
        for args in (out, inn):
            assert args[args.index("replay-window") + 1] == str(XFRM_REPLAY_WINDOW)

    def test_the_sa_uses_extended_sequence_numbers(self) -> None:
        out, inn = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)
        for args in (out, inn):
            assert args[args.index("flag") + 1] == "esn"

    def test_the_window_is_a_multiple_of_32(self) -> None:
        # The kernel keeps the ESN window as a bitmap of 32-bit words.
        assert XFRM_REPLAY_WINDOW % 32 == 0

    def test_replay_settings_precede_the_key(self) -> None:
        # `ip xfrm state add ... aead ALG KEY ICV` takes the rest of the line, so anything after
        # `aead` is read as part of the algorithm arguments and silently changes nothing.
        out, _ = xfrm_state_add_args("10.0.0.1", "10.0.0.2", _KEY)
        assert out.index("replay-window") < out.index("aead")
        assert out.index("flag") < out.index("aead")


class TestOwnedChains:
    """The rules live in chains this backend owns. `iptables -C` answers "is the rule present",
    which is not the question that decides whether it runs -- an ACCEPT inserted above a bare
    INPUT rule bypasses it while the check still passes."""

    def test_jump_is_first_reads_the_head_of_the_builtin(self) -> None:
        listing = f"-P INPUT ACCEPT\n-A INPUT -j {CHAIN_IN}\n-A INPUT -j DOCKER-USER\n"
        assert jump_is_first(listing, "INPUT", CHAIN_IN) is True

    def test_a_displaced_jump_is_not_first(self) -> None:
        listing = f"-P INPUT ACCEPT\n-A INPUT -j DOCKER-USER\n-A INPUT -j {CHAIN_IN}\n"
        assert jump_is_first(listing, "INPUT", CHAIN_IN) is False

    def test_a_missing_jump_is_not_first(self) -> None:
        assert jump_is_first("-P INPUT ACCEPT\n", "INPUT", CHAIN_IN) is False

    def test_other_chains_in_the_listing_are_ignored(self) -> None:
        listing = f"-N {CHAIN_IN}\n-A {CHAIN_IN} -j DROP\n-A INPUT -j {CHAIN_IN}\n"
        assert jump_is_first(listing, "INPUT", CHAIN_IN) is True

    async def test_setup_installs_every_chain_and_its_jump(self) -> None:
        rec = _AbsentRuleRecorder()
        plugin = _plugin(rec, reader=_Listing(lambda argv: ""))
        await plugin.setup_session_network(_ENC_META, _SELF)
        for table, builtin, chain in OWNED_CHAINS:
            assert ["iptables", "-t", table, "-N", chain] in rec.calls
            assert ["iptables", "-t", table, "-I", builtin, "1", "-j", chain] in rec.calls

    async def test_a_displaced_jump_is_moved_back_to_the_head(self) -> None:
        displaced = _Listing(
            lambda argv: "-P INPUT ACCEPT\n-A INPUT -j SOMEONE-ELSE\n-A INPUT -j BAI-VXLAN-IN\n"
        )
        rec = _AbsentRuleRecorder()
        plugin = _plugin(rec, reader=displaced)
        await plugin.setup_session_network(_ENC_META, _SELF)
        # Removed before being re-inserted, so restoring the order does not leave a duplicate.
        assert ["iptables", "-t", "filter", "-D", "INPUT", "-j", CHAIN_IN] in rec.calls
        assert ["iptables", "-t", "filter", "-I", "INPUT", "1", "-j", CHAIN_IN] in rec.calls

    async def test_a_jump_already_at_the_head_is_left_alone(self) -> None:
        rec = _AbsentRuleRecorder()
        plugin = _plugin(rec)  # the default listing already has our jump first
        await plugin.setup_session_network(_ENC_META, _SELF)
        assert ["iptables", "-t", "filter", "-D", "INPUT", "-j", CHAIN_IN] not in rec.calls

    async def test_the_chains_survive_a_session_ending(self) -> None:
        # Their lifetime is the process's, not a session's -- see TestChainsAreProcessScoped.
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        second = replace(_ENC_META, session_id="s2", vni=4098)
        await plugin.setup_session_network(second, _SELF)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert ["iptables", "-t", "filter", "-X", CHAIN_IN] not in rec.calls


class TestEgressGuard:
    """MARK is not a terminating target: any later rule in the same hook can clear it, after which
    the XFRM policy no longer matches and the frame leaves in CLEAR TEXT with nothing reporting it.
    Measured in a pair of namespaces -- with the mark rule removed, 8 of 8 VXLAN frames left
    unencrypted; with this guard installed, 0 left and 0 were encrypted."""

    def test_the_guard_drops_only_unprotected_egress_of_this_vni(self) -> None:
        args = egress_guard_add_args(4097, 4789)
        assert args[:3] == ["iptables", "-A", CHAIN_GUARD]
        assert args[args.index("--u32") + 1] == "0>>22&0x3C@12>>8=4097"
        assert args[args.index("--dir") + 1] == "out"
        assert args[args.index("--pol") + 1] == "none"
        assert args[-2:] == ["-j", "DROP"]

    async def test_setup_installs_it_for_an_encrypted_session(self) -> None:
        rec = _AbsentRuleRecorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        assert egress_guard_add_args(4097, 4789) in rec.calls

    async def test_setup_leaves_an_unencrypted_session_alone(self) -> None:
        rec = _AbsentRuleRecorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_META, _SELF)
        assert egress_guard_add_args(4097, 4789) not in rec.calls

    async def test_setup_refuses_the_session_when_it_cannot_be_installed(self) -> None:
        class _NoGuard(Recorder):
            @override
            async def __call__(self, argv: Sequence[str]) -> None:
                await super().__call__(argv)
                if CHAIN_GUARD in argv and argv[1] in ("-C", "-A"):
                    raise RuntimeError("iptables: No chain/target/match by that name")

        rec = _NoGuard()
        plugin = _plugin(rec)
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.setup_session_network(_ENC_META, _SELF)

    async def test_the_drift_check_reasserts_it(self) -> None:
        rec = _AbsentRuleRecorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.ensure_session_security("s1", [])
        assert egress_guard_add_args(4097, 4789) in rec.calls

    async def test_teardown_removes_it(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert egress_guard_del_args(4097, 4789) in rec.calls


class TestTeardownKeepsOwnership:
    """ "Already gone" is the only failure teardown may call success. A permission error, a held
    xtables lock or an EBUSY device leaves real state on the host, and reporting that as done is
    what makes it permanent -- the caller drops its record and the manager hands the VNI on."""

    def test_absent_errors_are_classified(self) -> None:
        for text in (
            "command failed (rc=1): iptables -D: Bad rule (does a matching rule exist?)",
            "command failed (rc=1): iptables -X: No chain/target/match by that name",
            'command failed (rc=1): ip link del: Cannot find device "baivx4097"',
            "command failed (rc=2): ip xfrm state del: No such process",
        ):
            assert is_absent_error(RuntimeError(text)) is True

    def test_real_failures_are_not_classified_as_absent(self) -> None:
        for text in (
            "command failed (rc=4): iptables: Another app is currently holding the xtables lock",
            "command failed (rc=1): ip link del: Operation not permitted",
            "command failed (rc=1): ip link del: Device or resource busy",
            "command failed (rc=1): iptables: Permission denied (you must be root)",
        ):
            assert is_absent_error(RuntimeError(text)) is False

    def test_a_missing_tool_is_a_failure_not_an_absence(self) -> None:
        # `iptables` leaving PATH says nothing about whether the rules are still installed; it
        # says this node can no longer clean up, which is a failure to report.
        assert is_absent_error(FileNotFoundError("iptables")) is False

    async def test_a_failed_removal_raises_instead_of_reporting_success(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.fail_on = lambda argv: list(argv[:3]) == ["ip", "link", "del"]
        with pytest.raises(OverlayTeardownIncomplete):
            await plugin.teardown_session_network("s1")

    async def test_the_session_is_still_owned_after_a_failed_teardown(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.fail_on = lambda argv: list(argv[:3]) == ["ip", "link", "del"]
        with pytest.raises(OverlayTeardownIncomplete):
            await plugin.teardown_session_network("s1")
        # Retryable: the record the retry needs is still here.
        assert plugin.security_state("s1") is not None

    async def test_a_retry_after_the_fault_clears_completes(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.fail_on = lambda argv: list(argv[:3]) == ["ip", "link", "del"]
        with pytest.raises(OverlayTeardownIncomplete):
            await plugin.teardown_session_network("s1")
        rec.fail_on = None
        await plugin.teardown_session_network("s1")
        assert plugin.security_state("s1") is None

    async def test_an_already_absent_object_does_not_block_teardown(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)

        async def _gone(argv: Sequence[str]) -> None:
            rec.calls.append(list(argv))
            if list(argv[:3]) == ["ip", "link", "del"]:
                raise RuntimeError('Cannot find device "baivx4097"')

        plugin._runner = _gone
        await plugin.teardown_session_network("s1")
        assert plugin.security_state("s1") is None


class TestTeardownRetryFindsThePairAgain:
    """A failed XFRM delete is only retryable if the retry can still find the pair. The
    bookkeeping the retry reads (`_encrypted_peers`) must therefore outlive the failure --
    otherwise the retry finds nothing to do, succeeds, and the manager releases the VNI over an
    SA and policy still on the host."""

    async def test_a_failed_xfrm_delete_keeps_the_peer_for_the_retry(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.fail_on = lambda argv: list(argv[:4]) == ["ip", "xfrm", "state", "del"]
        with pytest.raises(OverlayTeardownIncomplete):
            await plugin.teardown_session_network("s1")
        assert plugin.encrypted_peers("s1") == frozenset({_PEER.vtep_ip})

    async def test_the_retry_reissues_the_same_deletes(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.fail_on = lambda argv: list(argv[:4]) == ["ip", "xfrm", "state", "del"]
        with pytest.raises(OverlayTeardownIncomplete):
            await plugin.teardown_session_network("s1")
        rec.fail_on = None
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert any(list(c[:4]) == ["ip", "xfrm", "state", "del"] for c in rec.calls), (
            "the retry did not attempt the XFRM deletes again; it would have reported success"
            " over an SA and policy still on this host"
        )
        assert plugin.encrypted_peers("s1") == frozenset()

    async def test_a_missing_tool_is_not_treated_as_already_cleaned_up(self) -> None:
        # `ip` disappearing from PATH says nothing about whether the devices are still there.
        assert is_absent_error(FileNotFoundError("ip")) is False


class TestChainsAreProcessScoped:
    """The chains are host-global and shared, but the only record of who needs them is this
    process's `_sessions`, which a session joins AFTER its rules are installed. Deciding to
    remove them from that record can therefore look during the gap and strip a session that had
    just finished protecting itself."""

    async def test_teardown_does_not_remove_the_chains(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        for table, _builtin, chain in OWNED_CHAINS:
            assert ["iptables", "-t", table, "-X", chain] not in rec.calls

    async def test_init_installs_them(self) -> None:
        rec = _AbsentRuleRecorder()
        plugin = _plugin(rec, reader=_Listing(lambda argv: ""))
        await plugin.init()
        for table, builtin, chain in OWNED_CHAINS:
            assert ["iptables", "-t", table, "-N", chain] in rec.calls
            assert ["iptables", "-t", table, "-I", builtin, "1", "-j", chain] in rec.calls

    async def test_cleanup_removes_them(self) -> None:
        rec = Recorder()
        plugin = _plugin(rec)
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        await plugin.cleanup()
        for table, _builtin, chain in OWNED_CHAINS:
            assert ["iptables", "-t", table, "-X", chain] in rec.calls


class TestUnclosedSurvivors:
    """`prepare_recovery` raising does not stop the privnet -- it continues in degraded mode so
    live sessions can retry their own transitions. A tunnel it could not bring down is then an
    open path that nothing owns, and the VNI naming it must not be built on."""

    async def test_setup_refuses_a_vni_whose_survivor_is_still_up(self) -> None:
        rec = Recorder(fail_on=lambda argv: list(argv[:3]) == ["ip", "link", "set"])
        plugin = _plugin(rec, vxlans={vxlan_dev(4097)})
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.prepare_recovery()
        assert plugin.unclosed_devices() == frozenset({vxlan_dev(4097)})
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.setup_session_network(_ENC_META, _SELF)

    async def test_setup_proceeds_once_the_survivor_is_finally_down(self) -> None:
        rec = Recorder(fail_on=lambda argv: list(argv[:3]) == ["ip", "link", "set"])
        plugin = _plugin(rec, vxlans={vxlan_dev(4097)})
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.prepare_recovery()
        rec.fail_on = None
        await plugin.setup_session_network(_ENC_META, _SELF)
        assert plugin.unclosed_devices() == frozenset()


class TestPairOwnershipIsNodeWide:
    """Two agent processes on one host share the ESP pair between the same node pair, and each
    has its own in-process refcount. The journal is what stops the first session to end from
    taking the other's protection with it."""

    async def test_another_agents_claim_stops_the_removal(self, tmp_path: Path) -> None:
        journal = PairJournal(tmp_path / "pairs")
        rec = Recorder()
        plugin = _plugin(rec, pair_journal=journal, journal_owner="agent-a")
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        # A co-located agent programs the same pair for its own session.
        async with journal.claiming(
            pair_key(_SELF.vtep_ip or "", _PEER.vtep_ip or "", 4789), "agent-b", "s9"
        ):
            pass

        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert not any(list(c[:4]) == ["ip", "xfrm", "state", "del"] for c in rec.calls), (
            "the pair's SAs were deleted while another agent on this host was still carried by"
            " them; its session goes dead until the next reconcile"
        )

    async def test_the_last_agent_on_the_node_does_remove_it(self, tmp_path: Path) -> None:
        journal = PairJournal(tmp_path / "pairs")
        rec = Recorder()
        plugin = _plugin(rec, pair_journal=journal, journal_owner="agent-a")
        await plugin.setup_session_network(_ENC_META, _SELF)
        await plugin.add_peer("s1", _PEER)
        rec.calls.clear()
        await plugin.teardown_session_network("s1")
        assert any(list(c[:4]) == ["ip", "xfrm", "state", "del"] for c in rec.calls)

    async def test_recovery_drops_the_claims_of_a_previous_life(self, tmp_path: Path) -> None:
        journal = PairJournal(tmp_path / "pairs")
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        async with journal.claiming(key, "agent-a", "gone"):
            pass
        plugin = _plugin(Recorder(), pair_journal=journal, journal_owner="agent-a")
        await plugin.prepare_recovery()
        assert await journal.users(key) == frozenset()


class TestUnclosedSurvivorsBlockEverything:
    """An unclosed tunnel shares the underlay port, the XFRM pairs and the firewall chains with
    whatever is set up next, so admitting a DIFFERENT VNI beside it is admitting a session onto
    state nobody owns."""

    async def test_a_different_vni_is_refused_too(self) -> None:
        rec = Recorder(fail_on=lambda argv: list(argv[:3]) == ["ip", "link", "set"])
        plugin = _plugin(rec, vxlans={vxlan_dev(4097)})
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.prepare_recovery()
        other = replace(_ENC_META, session_id="s2", vni=4098)
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.setup_session_network(other, _SELF)

    async def test_retry_reports_what_is_still_up(self) -> None:
        rec = Recorder(fail_on=lambda argv: list(argv[:3]) == ["ip", "link", "set"])
        plugin = _plugin(rec, vxlans={vxlan_dev(4097)})
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.prepare_recovery()
        assert await plugin.retry_fail_close() == frozenset({vxlan_dev(4097)})
        rec.fail_on = None
        assert await plugin.retry_fail_close() == frozenset()


class TestAnUnrecordableClaimFailsClosed:
    """The claim is what another agent process counts when it decides whether the pair is still in
    use. With ours not on disk it reads the pair as free and deletes the very SAs being installed,
    and a marker kept in this process cannot tell it otherwise."""

    async def test_the_pair_is_not_programmed(self, tmp_path: Path) -> None:
        blocked = tmp_path / "file"
        blocked.write_text("not a directory")
        rec = Recorder()
        plugin = _plugin(rec, pair_journal=PairJournal(blocked / "pairs"))
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.add_peer("s1", _PEER)
        assert not any(list(c[:4]) == ["ip", "xfrm", "state", "add"] for c in rec.calls)

    async def test_no_forwarding_path_is_opened(self, tmp_path: Path) -> None:
        # The FDB entry is what makes a frame leave for that peer; opening it with no SA is the
        # clear-text case the ordering exists to avoid.
        blocked = tmp_path / "file"
        blocked.write_text("not a directory")
        rec = Recorder()
        plugin = _plugin(rec, pair_journal=PairJournal(blocked / "pairs"))
        await plugin.setup_session_network(_ENC_META, _SELF)
        rec.calls.clear()
        with pytest.raises(OverlayEncryptionUnavailable):
            await plugin.add_peer("s1", _PEER)
        assert not any(list(c[:3]) == ["bridge", "fdb", "append"] for c in rec.calls)
