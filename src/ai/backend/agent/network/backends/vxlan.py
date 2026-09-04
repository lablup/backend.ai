"""VXLAN cluster-network backend (BEP-1062).

Portable default data plane: per-session VXLAN VNI + bridge, with unicast head-end
replication (FDB) driven by the SessionNetworkCoordinator's etcd membership watch.

The side-effecting ``ip``/``bridge`` invocations are isolated behind an injectable
runner; the command builders and CNI-config assembly are pure and unit-tested.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import hmac
import ipaddress
import logging
import os
import re
import shlex
import time
from collections.abc import Awaitable, Callable, Collection, Sequence
from dataclasses import dataclass
from typing import Any, Final, override

from ai.backend.agent.errors.network import (
    OverlayAddressNotAssigned,
    OverlayEncryptionUnavailable,
    OverlayMtuTooLarge,
    OverlayTeardownIncomplete,
)
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.network.backends.vxlan_security import (
    VxlanSecurityEvent,
    VxlanSecurityState,
    VxlanSecurityStateMachine,
)
from ai.backend.agent.network.caps import probe_caps
from ai.backend.agent.network.local_subnet import LocalSubnetAllocator, get_local_subnet_allocator
from ai.backend.agent.network.native_attacher import redirect_session_dns, remove_dns_redirect
from ai.backend.agent.network.overlay_probe import arp_probe
from ai.backend.agent.network.pair_journal import PairJournal, pair_key
from ai.backend.agent.network.path_mtu import underlay_mtu
from ai.backend.agent.network.readiness import conflicting_device
from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
from ai.backend.common.network.types import (
    DEFAULT_VXLAN_PORT,
    ESP_OVERHEAD,
    VXLAN_OVERHEAD,
    AgentNetworkCaps,
    AttachKind,
    EndpointPlan,
    Member,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
    mac_for_ip,
)
from ai.backend.common.types import ClusterInfo, KernelCreationConfig
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

VXLAN_DSTPORT = DEFAULT_VXLAN_PORT
"""Kept as the module-level default for the pure command builders. The value a live session
actually uses comes from ``SessionNetMeta.vxlan_port``, so both ends of a tunnel agree."""
OVERLAY_IFNAME = "baimulti0"
_BROADCAST_MAC = "00:00:00:00:00:00"

Runner = Callable[[Sequence[str]], Awaitable[None]]
#: Runs a command and returns its stdout. Separate from ``Runner`` because the firewall
#: needs to READ its own rule order to keep it, and every other command here only writes.
Reader = Callable[[Sequence[str]], Awaitable[str]]
MtuProbe = Callable[[str], Awaitable[int | None]]
# (bridge, target_ip, target_mac) -> answered? / None when the probe could not run.
ReachProbe = Callable[[str, str, str], Awaitable[bool | None]]
KeyGeneration = Callable[[], int]
#: The name of every VXLAN device on this host.
VxlanLister = Callable[[], Awaitable[Collection[str]]]

# A freshly published endpoint may belong to a container that is still starting, so the reach
# probe is retried before it is believed. Cheap (one ARP frame each) and bounded.
_REACH_ATTEMPTS: Final = 5
_REACH_RETRY_DELAY_SEC: Final = 3.0


# --- naming (kept within the 15-char interface name limit) ---


#: Prefix of every vxlan device this backend creates; recovery uses it as the durable ownership
#: boundary before the process has reconstructed session metadata.
VXLAN_DEV_PREFIX: Final = "baivx"


def vxlan_dev(vni: int) -> str:
    return f"{VXLAN_DEV_PREFIX}{vni}"


def bridge_dev(vni: int) -> str:
    return f"baibr{vni}"


# --- pure command builders ---


def vxlan_link_add_args(
    vni: int,
    uplink: str,
    *,
    local: str | None = None,
    mtu: int | None = None,
    dstport: int = VXLAN_DSTPORT,
) -> list[str]:
    # ``local`` pins the tunnel's outer source address. Without it the kernel picks one per route
    # (ip-link(8): the source is chosen automatically when `local` is omitted), so on a host with
    # more than one address on the uplink the frames can leave from an address that is not the VTEP
    # this node published. Peers then hold an FDB entry for one address and receive from another,
    # and — worse — the ESP policy's selector is written against the published pair, so traffic
    # that leaves from the other address matches no policy and goes out in clear text. The whole
    # overlay is keyed on this address being the one peers were told about; say so to the kernel.
    # ``mtu`` is the OVERLAY MTU (the inner frame the tunnel carries), which the manager already
    # computed as underlay - overhead. Setting it explicitly ties the vxlan device, the overlay
    # bridge and the container NIC to one value instead of relying on the kernel's auto-calc
    # (uplink - 50) happening to match — which silently diverges the moment this node's uplink MTU
    # differs from the manager's assumption, reopening the black hole.
    # ``mtu`` is a generic link property and MUST precede ``type vxlan``: after it, ``ip`` parses
    # the next token (our ``id``) as a vxlan sub-option and errors out. Verified against iproute2.
    mtu_args = ["mtu", str(mtu)] if mtu is not None else []
    local_args = ["local", local] if local else []
    return [
        "ip", "link", "add", vxlan_dev(vni), *mtu_args,
        "type", "vxlan",
        "id", str(vni),
        "dev", uplink,
        *local_args,
        "dstport", str(dstport),
        "nolearning",
    ]  # fmt: skip


def bridge_link_add_args(vni: int, *, mtu: int | None = None) -> list[str]:
    mtu_args = ["mtu", str(mtu)] if mtu is not None else []
    return ["ip", "link", "add", bridge_dev(vni), *mtu_args, "type", "bridge"]


def set_master_args(vni: int) -> list[str]:
    return ["ip", "link", "set", vxlan_dev(vni), "master", bridge_dev(vni)]


def link_up_args(dev: str) -> list[str]:
    return ["ip", "link", "set", dev, "up"]


def link_down_args(dev: str) -> list[str]:
    return ["ip", "link", "set", dev, "down"]


def link_del_args(dev: str) -> list[str]:
    return ["ip", "link", "del", dev]


def fdb_append_args(vni: int, dst: str, *, mac: str = _BROADCAST_MAC) -> list[str]:
    return ["bridge", "fdb", "append", mac, "dev", vxlan_dev(vni), "dst", dst]


def fdb_del_args(vni: int, dst: str, *, mac: str = _BROADCAST_MAC) -> list[str]:
    return ["bridge", "fdb", "del", mac, "dev", vxlan_dev(vni), "dst", dst]


# --- proactive endpoint programming (unicast FDB + ARP; replaces BUM flooding) ---


def fdb_replace_args(vni: int, mac: str, dst: str) -> list[str]:
    """Program the exact unicast MAC→VTEP forwarding entry for a known remote endpoint."""
    return ["bridge", "fdb", "replace", mac, "dev", vxlan_dev(vni), "dst", dst]


# --- overlay encryption: kernel IPSec (ESP/AES-GCM) on the VXLAN tunnel (overlay-encryption.md) ---
# The crypto is the kernel's (XFRM/ESP + AES-NI); these only build the `ip xfrm` control-plane
# commands the privnet runs beside the FDB entry. Transport-mode ESP between the two VTEPs encrypts
# the VXLAN UDP (4789) — the L2 overlay is untouched.

_ICV_BITS = 128  # AES-GCM authentication tag length
# Host-global XFRM ownership identifiers. These deliberately differ from Docker/libnetwork's
# 0xD0C4E3: Docker removes every policy with its mark and every SA with its reqid, and an equal
# selector is updated in place. Sharing its values would therefore let either implementation
# replace or delete the other's protection when both use the default UDP port on one host.
XFRM_MARK: Final = 0xBA100001
XFRM_REQID: Final = 0xBA100002
_XFRM_MARK: Final = f"{XFRM_MARK:#x}"
_XFRM_MARK_MASK: Final = "0xffffffff"
# Anti-replay. A new SA defaults to `replay-window 0` -- no window at all, so a replayed ESP
# packet is accepted -- and to 32-bit sequence numbers, which a non-ESN SA does not wrap: it
# errors and the tunnel stops. At 100k packet/s that ceiling is ~11.9 hours, inside the rotation
# interval below, and GSO spends one sequence number per segment. ESN moves the counter to 64
# bits (the high half is covered by the ICV but not transmitted) and takes the window with it.
# Both ends derive these identically, so there is nothing to negotiate -- but an agent that
# predates this cannot decrypt an ESN peer's traffic, so the two must not be mixed in one cluster.
XFRM_REPLAY_WINDOW: Final = 128
#: How often the node re-asserts every encrypted session's protection. Short, because
#: the window it leaves is one in which injected plaintext is accepted or -- if the
#: mark went with the rules -- traffic stops; affordable, because one pass reads the
#: whole node's state in four commands and changes only what drifted.
PROTECTION_INTERVAL_SEC: Final = 3.0
KEY_ROTATION_INTERVAL_SEC: Final = 12 * 60 * 60
_KEYRING_SIZE: Final = 3
_VXLAN_LINE: Final = re.compile(r"^\d+:\s+(?P<name>[^:@\s]+)")


async def _list_vxlan_devices() -> frozenset[str]:
    """The name of every VXLAN device on this host.

    Names only, and deliberately without `ip -d`. Both callers ask one question -- does this device
    still exist -- and the attribute dump that would answer more is the part that breaks: measured
    on three nodes running the same iproute2 6.1.0 on Ubuntu 24.04, `ip -d -j link show type vxlan`
    is valid JSON on kernel 6.8, emits malformed JSON on 6.14 (a `fan-map` value written into the
    object with no key: `"id":60001fan-map ,"link":...`), and emits nothing at all on 6.17. So a
    cluster that works today breaks on a kernel upgrade, in two different ways. The plain
    `ip -o link show type vxlan` line format is the same on all three.

    Recovery relies on this to fail-close unknown surviving tunnels, so a failure is surfaced
    rather than represented as an empty host.
    """
    proc = await asyncio.create_subprocess_exec(
        "ip",
        "-o",
        "link",
        "show",
        "type",
        "vxlan",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    out, _ = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"could not enumerate VXLAN links (rc={proc.returncode})")
    names: set[str] = set()
    for line in (out or b"").decode(errors="replace").splitlines():
        # "<index>: <name>[@<parent>]: <FLAGS> ..." -- the one part of `ip link` output that has
        # not changed across the kernels above.
        if (match := _VXLAN_LINE.match(line)) is not None:
            names.add(match.group("name"))
    return frozenset(names)


def _esp_spi(src: str, dst: str, generation: int = 0) -> int:
    """A deterministic 32-bit SPI for the directed VTEP pair, so both ends agree without a
    handshake: A's out-SA (src=A,dst=B) and B's in-SA (src=A,dst=B) compute the same value.

    The pair and one of three generation slots are the whole input. It used to fold the VNI in as
    well, but every session between these two nodes wants the same pair-generation SA and traffic
    key. Folding the VNI in would manufacture several equivalent SAs for one policy to choose
    between, recreating the ambiguity this design removes.

    Kept above 255 (SPIs 0-255 are reserved). Three slots bound the kernel state while letting the
    previous, current and next traffic-key generations coexist across a rotation boundary."""
    slot = generation % _KEYRING_SIZE
    digest = hashlib.sha256(f"{src}:{dst}:slot:{slot}".encode()).digest()
    return (int.from_bytes(digest[:4], "big") % (2**32 - 256)) + 256


def _aead_key(key_hex: str, spi: int) -> str:
    """rfc4106(gcm(aes)) keys carry a 4-byte salt after the cipher key, and the GCM nonce is that
    salt followed by the 8-byte per-packet IV. Derive the salt from the key *and the SPI* -- both
    ends compute the same one for a given SA, and no two SAs get the same one.

    Deriving it from the key alone gave every SA on the node, in both directions and to every peer,
    one shared salt. RFC 4106 asks for a distinct salt per SA precisely so that a repeated IV cannot
    become a repeated nonce, and Moby folds the SPI in for the same reason. Measured: on Linux the
    nonces did not actually collide, because the kernel gives each SA an independent random IV base
    (a delete-and-recreate of the same key/salt/SPI produced a different one) -- but that is the
    kernel's choice to make, not a property of what is programmed here. This makes it structural.
    """
    salt = hashlib.sha256(bytes.fromhex(key_hex) + spi.to_bytes(4, "big")).digest()[:4]
    return "0x" + key_hex + salt.hex()


def _pair_key(cluster_key_hex: str, self_vtep: str, peer_vtep: str, generation: int = 0) -> str:
    """The cipher key for one node pair, derived from the cluster secret.

    The SA is already per node pair -- `_esp_spi` folds the VTEP pair and nothing else -- so there
    is no reason for the bytes in it to be the cluster's. What went in before was the secret
    itself, verbatim, on every SA on every node; and `ip xfrm state` prints an SA's key back in the
    clear, so one reader on any node held the material protecting every pair in the cluster. Per
    pair and generation, that reader holds one pair's time-bounded traffic key.

    It is not a trust boundary -- anything holding the cluster secret derives them all -- only a
    blast radius. Unordered, so both ends of a pair reach the same value with no handshake, exactly
    as the SPI and the salt already do. HMAC rather than a bare hash: the standard construction for
    deriving from a secret, and the input is attacker-visible (VTEP addresses).
    """
    lo, hi = sorted((self_vtep, peer_vtep))
    return hmac.new(
        bytes.fromhex(cluster_key_hex),
        f"bai-overlay-pair:{lo}|{hi}|generation:{generation}".encode(),
        hashlib.sha256,
    ).hexdigest()


def xfrm_state_add_args(
    self_vtep: str,
    peer_vtep: str,
    cluster_key_hex: str,
    *,
    generation: int = 0,
) -> list[list[str]]:
    """The ESP SA pair for this ordered VTEP pair -- one pair per node pair, shared by every
    session between them, which is what makes it safe for one policy to select it.

    The cluster secret is what arrives in the session meta; what reaches the kernel is the key
    derived from it for this pair and generation (see `_pair_key`)."""
    spi_out_n = _esp_spi(self_vtep, peer_vtep, generation)
    spi_in_n = _esp_spi(peer_vtep, self_vtep, generation)
    spi_out, spi_in = f"{spi_out_n:#x}", f"{spi_in_n:#x}"
    key_hex = _pair_key(cluster_key_hex, self_vtep, peer_vtep, generation)
    # One salt per SA, so the two directions never share a (key, salt) pair.
    aead_out = ["aead", "rfc4106(gcm(aes))", _aead_key(key_hex, spi_out_n), str(_ICV_BITS)]
    aead_in = ["aead", "rfc4106(gcm(aes))", _aead_key(key_hex, spi_in_n), str(_ICV_BITS)]
    # `flag esn` is rejected without a window, so the two are one setting, not two.
    replay = ["replay-window", str(XFRM_REPLAY_WINDOW), "flag", "esn"]
    return [
        ["ip", "xfrm", "state", "add", "src", self_vtep, "dst", peer_vtep,
         "proto", "esp", "spi", spi_out, "reqid", f"{XFRM_REQID:#x}",
         "mode", "transport", *replay, *aead_out],
        ["ip", "xfrm", "state", "add", "src", peer_vtep, "dst", self_vtep,
         "proto", "esp", "spi", spi_in, "reqid", f"{XFRM_REQID:#x}",
         "mode", "transport", *replay, *aead_in],
    ]  # fmt: skip


def xfrm_policy_add_args(
    self_vtep: str,
    peer_vtep: str,
    *,
    dstport: int = VXLAN_DSTPORT,
    generation: int = 0,
) -> list[list[str]]:
    """The outbound policy selecting this node<->peer VXLAN UDP for ESP.

    NOT per session, and it cannot be: the selector is the OUTER packet (src/dst IP, udp dport) and
    the VNI lives inside the UDP payload, where no XFRM selector can reach it. So every session
    between the same two nodes on the same port shares one policy — which is why the caller
    refcounts it instead of deleting it with whichever session ends first. The SA it selects is
    shared the same way (see the state args above), so "which one" is no longer a question.

    The receive path deliberately has no inbound XFRM policy. The inbound SA authenticates and
    decrypts ESP, while the INPUT policy-match rule below drops VXLAN packets with no XFRM secpath.
    This matches Docker Swarm's split between outbound XFRM selection and inbound filtering.
    """
    return [
        ["ip", "xfrm", "policy", "update", "src", self_vtep, "dst", peer_vtep,
         "proto", "udp", "dport", str(dstport), "dir", "out",
         "mark", _XFRM_MARK, "mask", _XFRM_MARK_MASK,
         "tmpl", "src", self_vtep, "dst", peer_vtep, "proto", "esp",
         "spi", f"{_esp_spi(self_vtep, peer_vtep, generation):#x}",
         "reqid", f"{XFRM_REQID:#x}", "mode", "transport"],
    ]  # fmt: skip


def xfrm_state_del_args(self_vtep: str, peer_vtep: str, *, generation: int = 0) -> list[list[str]]:
    spi_out = f"{_esp_spi(self_vtep, peer_vtep, generation):#x}"
    spi_in = f"{_esp_spi(peer_vtep, self_vtep, generation):#x}"
    return [
        ["ip", "xfrm", "state", "del", "src", self_vtep, "dst", peer_vtep, "proto", "esp",
         "spi", spi_out],
        ["ip", "xfrm", "state", "del", "src", peer_vtep, "dst", self_vtep, "proto", "esp",
         "spi", spi_in],
    ]  # fmt: skip


def xfrm_policy_del_args(
    self_vtep: str, peer_vtep: str, *, dstport: int = VXLAN_DSTPORT
) -> list[list[str]]:
    return [
        ["ip", "xfrm", "policy", "del", "src", self_vtep, "dst", peer_vtep,
         "proto", "udp", "dport", str(dstport), "dir", "out",
         "mark", _XFRM_MARK, "mask", _XFRM_MARK_MASK],
    ]  # fmt: skip


def xfrm_add_args(
    self_vtep: str,
    peer_vtep: str,
    key_hex: str,
    *,
    dstport: int = VXLAN_DSTPORT,
    generation: int = 0,
) -> list[list[str]]:
    """The `ip xfrm` commands that encrypt this node↔peer VXLAN traffic: an out/in ESP SA pair plus
    the outbound policy selecting the VXLAN UDP.

    The states use `add`, not `update`: `XFRM_MSG_UPDSA` looks the SA up first and returns ESRCH
    when it is absent, so `update` alone never *creates* one -- measured, every call failed with
    "RTNETLINK answers: No such process" and the overlay ran in clear text while still paying the
    38-byte ESP MTU cost. `add` is EEXIST on an SA that survived an agent restart, which
    `_run_xfrm` handles by replaying it as `update`. Policies keep `update`, which is a true
    upsert (`XFRM_MSG_UPDPOLICY` creates when absent).
    """
    return [
        *xfrm_state_add_args(self_vtep, peer_vtep, key_hex, generation=generation),
        *xfrm_policy_add_args(self_vtep, peer_vtep, dstport=dstport, generation=generation),
    ]


def xfrm_del_args(
    self_vtep: str,
    peer_vtep: str,
    *,
    dstport: int = VXLAN_DSTPORT,
    generation: int | None = None,
) -> list[list[str]]:
    generations = range(_KEYRING_SIZE) if generation is None else (generation,)
    return [
        *[
            args
            for key_generation in generations
            for args in xfrm_state_del_args(self_vtep, peer_vtep, generation=key_generation)
        ],
        *xfrm_policy_del_args(self_vtep, peer_vtep, dstport=dstport),
    ]


def neigh_replace_args(vni: int, ip: str, mac: str) -> list[str]:
    """Program a permanent ARP entry (IP→MAC) on the overlay bridge.

    This covers traffic the HOST originates onto the overlay. It does not suppress the containers'
    own ARP: the entry sits on the bridge in the host netns, and the vxlan device carries no
    ``proxy`` flag, so a container's broadcast ARP is still flooded to every peer VTEP by head-end
    replication. That works (which is why cross-node traffic passes), but the flooding is real and
    grows with the peer count. Actual suppression would mean ``proxy`` on the vxlan device with the
    neighbour entries moved onto it — a behaviour change worth measuring before making.
    """
    return ["ip", "neigh", "replace", ip, "lladdr", mac, "dev", bridge_dev(vni), "nud", "permanent"]


def neigh_del_args(vni: int, ip: str) -> list[str]:
    return ["ip", "neigh", "del", ip, "dev", bridge_dev(vni)]


# --- overlay-bridge FORWARD accept (survive a DROP FORWARD policy) ---
#
# With br_netfilter loaded and net.bridge.bridge-nf-call-iptables=1 (a node co-hosting Docker or
# kube-proxy, or a hardened host), frames bridged WITHIN the overlay bridge -- container veth <->
# vxlan device -- traverse the iptables FORWARD chain. If its policy is DROP (Docker sets exactly
# that), the overlay goes silently dead: handshakes and cross-node traffic are dropped with no
# ICMP. Accept intra-bridge forwarding on the overlay bridge, the same rule Docker installs for its
# own bridges. ``-i BR -o BR`` is exactly the intra-bridge path and nothing else (the encapsulated
# UDP leaves via the host's OUTPUT chain, not FORWARD).


def _forward_accept_rule(vni: int) -> list[str]:
    br = bridge_dev(vni)
    return ["FORWARD", "-i", br, "-o", br, "-j", "ACCEPT"]


def forward_accept_check_args(vni: int) -> list[str]:
    return ["iptables", "-C", *_forward_accept_rule(vni)]


def forward_accept_add_args(vni: int) -> list[str]:
    return ["iptables", "-I", *_forward_accept_rule(vni)]


def forward_accept_del_args(vni: int) -> list[str]:
    return ["iptables", "-D", *_forward_accept_rule(vni)]


# --- drop plaintext VXLAN for an encrypted VNI ---
#
# ESP protects what this node *sends*, and nothing else. A vxlan device accepts any well-formed
# frame that arrives on its UDP port carrying its VNI, decrypted or not, so an encrypted session
# stays wide open on the receive side: anyone who can reach the underlay port -- an unregistered
# host, a node evicted from the session, a co-tenant on the same L2 -- injects a plaintext frame
# with the right VNI and it lands on the overlay bridge as if a member had sent it. Measured on
# three nodes: a host that was never a member injected plaintext VNI 4097 into an encrypted
# session and the member accepted it (0% loss) and replied in clear text.
#
# So the receive side has to be closed explicitly, which is what Docker's overlay driver does too:
# for an encrypted VNI, drop VXLAN that did *not* arrive inside an SA. ``-m policy --dir in
# --pol none`` is the half that distinguishes them -- an ESP-decapsulated frame carries its
# policy state into INPUT and does not match ``none``, while an injected one does.
#
# ``u32`` picks the VNI out of the encapsulation: ``0>>22&0x3C`` is the IP header length, which
# lands the cursor on the UDP header, and ``@12`` is the VXLAN VNI word (UDP header 8 + VXLAN
# flags/reserved 4); ``>>8`` drops the trailing reserved byte. The offset was calibrated against
# real frames rather than derived -- candidate LOG rules at 8, 12 and 16 were installed together
# and only 12 matched.
#
# Per-VNI rather than per-port: two sessions can share the underlay port with only one of them
# encrypted, and a port-wide rule would black-hole the other.


# The rules live in chains this backend owns, jumped to from the head of the built-in chain.
# Two reasons, both measured: a co-tenant's ``iptables -F INPUT`` takes an unowned rule with it,
# and rule ORDER is what decides whether ours runs at all -- an ACCEPT inserted above a bare
# INPUT rule bypasses it while ``iptables -C`` still reports the rule present. Owning the chain
# reduces drift to one question ("is our jump still first?"), which reconcile can answer and fix.
CHAIN_IN: Final = "BAI-VXLAN-IN"  # filter, from INPUT: drop injected plaintext
CHAIN_GUARD: Final = "BAI-VXLAN-GUARD"  # filter, from OUTPUT: drop unencrypted egress
CHAIN_MARK: Final = "BAI-VXLAN-MARK"  # mangle, from OUTPUT: mark for the XFRM policy
#: (table, built-in chain, our chain), in the order they are installed.
OWNED_CHAINS: Final = (
    ("filter", "INPUT", CHAIN_IN),
    ("filter", "OUTPUT", CHAIN_GUARD),
    ("mangle", "OUTPUT", CHAIN_MARK),
)


def _vni_match(vni: int, dstport: int) -> list[str]:
    return ["-p", "udp", "--dport", str(dstport), "-m", "u32", "--u32", f"0>>22&0x3C@12>>8={vni}"]


def chain_create_args(table: str, chain: str) -> list[str]:
    return ["iptables", "-t", table, "-N", chain]


def chain_delete_args(table: str, chain: str) -> list[str]:
    return ["iptables", "-t", table, "-X", chain]


def chain_flush_args(table: str, chain: str) -> list[str]:
    return ["iptables", "-t", table, "-F", chain]


def chain_list_args(table: str, chain: str) -> list[str]:
    return ["iptables", "-t", table, "-S", chain]


def jump_check_args(table: str, builtin: str, chain: str) -> list[str]:
    return ["iptables", "-t", table, "-C", builtin, "-j", chain]


def jump_add_args(table: str, builtin: str, chain: str) -> list[str]:
    return ["iptables", "-t", table, "-I", builtin, "1", "-j", chain]


def jump_del_args(table: str, builtin: str, chain: str) -> list[str]:
    return ["iptables", "-t", table, "-D", builtin, "-j", chain]


@dataclass(frozen=True)
class ProtectionSnapshot:
    """One read of everything the protection re-assert needs to decide, for the WHOLE node.

    Four commands, whatever the session count. The check used to be per session and per peer,
    every three seconds, reprogramming unconditionally: roughly 21 iptables processes plus 13 per
    peer for each encrypted session, which at a hundred sessions is over a thousand subprocesses a
    second -- and the xtables lock contention that produces is itself read as a protection
    failure, so the loop meant to keep tunnels up starts taking them down.
    """

    filter_rules: str
    mangle_rules: str
    #: (src, dst, spi) of the ESP SAs this backend owns, matched on its own reqid.
    sa_endpoints: frozenset[tuple[str, str, int]]
    #: (src, dst, dport) of the outbound policies carrying this backend's mark.
    policy_pairs: frozenset[tuple[str, str, int]]
    #: VXLAN devices that are administratively UP. A device this node believes is carrying can be
    #: DOWN because a co-located agent restarted and its fail-close preflight downs every
    #: `baivx*` on the host, ours included -- and nothing else ever looks.
    up_devices: frozenset[str]

    def table(self, table: str) -> str:
        return self.mangle_rules if table == "mangle" else self.filter_rules


def rule_is_present(listing: str, expected: Sequence[str]) -> bool:
    """Whether ``expected`` -- a rule as this backend builds it -- is in force in the chain.

    In force, not merely present. Two things beyond "is the text there":

    * The rule is compared as a normalised token sequence, because `iptables-save` renders the
      same rule differently from how it was written (`--u32` in hex, `MARK --set-mark` as
      `--set-xmark <mark>/<mask>`, `-p udp` gaining `-m udp`). A string match finds nothing, so
      every rule looks missing and the pass reprograms the whole node every tick.
    * It must be the FIRST rule in that chain selecting this traffic. A DROP with an ACCEPT for
      the same VNI above it is not protection -- the packet never reaches it -- and checking only
      for existence reports the session protected while injected plaintext walks past.
    """
    wanted = _normalise_rule(expected)
    selector = _traffic_selector(wanted)
    chain = expected[0]
    for line in listing.splitlines():
        stripped = line.strip()
        if not stripped.startswith(f"-A {chain} "):
            continue
        try:
            found = _normalise_rule(shlex.split(stripped)[1:])
        except ValueError:
            continue
        if _traffic_selector(found) != selector:
            continue  # a rule about other traffic; it does not shadow ours
        return found == wanted
    return False


def _traffic_selector(tokens: Sequence[str]) -> tuple[str, ...]:
    """The part of a rule that decides WHICH packets it sees, without its target or match modules.

    Two rules with the same selector are about the same traffic, so whichever comes first decides
    what happens to it.
    """
    out: list[str] = []
    index = 1  # skip the chain
    while index < len(tokens):
        token = tokens[index]
        if token in ("-p", "--dport", "--sport", "--u32") and index + 1 < len(tokens):
            out.extend((token, tokens[index + 1]))
            index += 2
            continue
        index += 1
    return tuple(out)


def _normalise_rule(tokens: Sequence[str]) -> tuple[str, ...]:
    """One rule reduced to what identifies it, in the form both spellings agree on."""
    out: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "-m" and index + 1 < len(tokens) and tokens[index + 1] in ("udp", "tcp"):
            index += 2  # `-p udp` implies it; iptables-save writes it and we do not
            continue
        if token == "--u32" and index + 1 < len(tokens):
            out.extend(("--u32", _normalise_u32(tokens[index + 1])))
            index += 2
            continue
        if token in ("--set-mark", "--set-xmark") and index + 1 < len(tokens):
            mark, _, mask = tokens[index + 1].partition("/")
            # The mask is part of it: `--set-xmark 0xba100001/0xffffffff` and
            # `--set-xmark 0xba100001/0x0000ffff` set different bits, and the XFRM policy selects
            # on the whole value.
            # `--set-mark X` with no mask sets every bit of the value and clears none of the
            # others -- which iptables renders back as `--set-xmark X/0xffffffff`. Defaulting the
            # mask to the value instead makes the rule we wrote and the rule iptables reports look
            # different, so the pass reprograms it on every tick.
            out.extend(("--set-mark", str(int(mark, 0)), str(int(mask, 0) if mask else 0xFFFFFFFF)))
            index += 2
            continue
        out.append(token)
        index += 1
    return tuple(out)


def _normalise_u32(expression: str) -> str:
    """The WHOLE u32 expression with every literal in one base.

    Not just the value it compares against: `0>>22&0x3C@12>>8=4097` and
    `0>>22&0x3C@16>>8=4097` read different words of the packet, and keeping only the right-hand
    side would call the second one this rule.
    """
    out: list[str] = []
    number = ""
    for char in expression.strip('"'):
        if char.isalnum() or (char == "x" and number):
            number += char
            continue
        if number:
            out.append(_as_int_text(number))
            number = ""
        out.append(char)
    if number:
        out.append(_as_int_text(number))
    return "".join(out)


def _as_int_text(token: str) -> str:
    try:
        return str(int(token, 0))
    except ValueError:
        return token


def parse_up_vxlan_devices(listing: str) -> frozenset[str]:
    """Names of the VXLAN devices that are administratively UP, from `ip -o link show type vxlan`.

    The flags, not `state`: a device with no peer traffic reports `state UNKNOWN` while being
    perfectly up, and only the `UP` flag says whether it was administratively raised.
    """
    up: set[str] = set()
    for line in listing.splitlines():
        match = _VXLAN_LINE.match(line)
        if match is None:
            continue
        flags = line.partition("<")[2].partition(">")[0]
        if "UP" in flags.split(","):
            up.add(match.group("name"))
    return frozenset(up)


def parse_owned_sa_endpoints(listing: str, reqid: int) -> frozenset[tuple[str, str, int]]:
    """(src, dst, spi) of the ESP SAs carrying ``reqid``, from `ip xfrm state`.

    The endpoints, not the SPI alone: an SPI is derived from the pair, so checking it in isolation
    would accept an SA between the wrong two hosts as this pair's.
    """
    found: set[tuple[str, str, int]] = set()
    header: tuple[str, str] | None = None
    for line in listing.splitlines():
        if line.startswith("src "):
            tokens = line.split()
            dst = _value_after(tokens, "dst")
            header = (tokens[1].split("/")[0], dst.split("/")[0]) if dst is not None else None
            continue
        stripped = line.strip()
        if header is None or not stripped.startswith("proto esp"):
            continue
        tokens = stripped.split()
        spi = _value_after(tokens, "spi")
        found_reqid = _value_after(tokens, "reqid")
        if spi is None or found_reqid is None:
            continue
        try:
            if int(found_reqid, 0) == reqid:
                found.add((header[0], header[1], int(spi, 0)))
        except ValueError:
            continue
    return frozenset(found)


def parse_owned_policies(listing: str, mark: str) -> frozenset[tuple[str, str, int]]:
    """(src, dst, dport) of the OUTBOUND policies carrying ``mark``, from `ip xfrm policy`.

    The direction is part of it. This backend installs an out policy and nothing else, so an in
    or forward policy carrying the same mark is not what it is looking for -- and counting one
    would report the send path protected when only the receive path had a rule.
    """
    found: set[tuple[str, str, int]] = set()
    header: tuple[str, str, int] | None = None
    outbound = False
    marked = False
    for line in listing.splitlines():
        if line.startswith("src "):
            if header is not None and outbound and marked:
                found.add(header)
            tokens = line.split()
            dst = _value_after(tokens, "dst")
            dport = _value_after(tokens, "dport")
            header = (
                (tokens[1].split("/")[0], dst.split("/")[0], int(dport))
                if dst is not None and dport is not None and dport.isdigit()
                else None
            )
            outbound = marked = False
            continue
        if header is None:
            continue
        tokens = line.split()
        if _value_after(tokens, "dir") == "out":
            outbound = True
        if any(token.split("/")[0] == mark for token in tokens if token.startswith("0x")):
            marked = True
    if header is not None and outbound and marked:
        found.add(header)
    return frozenset(found)


def _value_after(tokens: Sequence[str], key: str) -> str | None:
    for index, token in enumerate(tokens):
        if token == key and index + 1 < len(tokens):
            return tokens[index + 1]
    return None


def jump_is_first(listing: str, builtin: str, chain: str) -> bool:
    """Whether our jump is the first rule of ``builtin`` in an ``iptables -S`` listing.

    Anything before it can ACCEPT the traffic and our chain never runs, which is the whole
    failure this ownership is meant to remove -- so "present" is not the question, "first" is.
    """
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) < 2 or parts[0] != "-A" or parts[1] != builtin:
            continue  # -P/-N lines and other chains
        return parts[-2:] == ["-j", chain]
    return False


def _plaintext_drop_rule(vni: int, dstport: int) -> list[str]:
    return [
        CHAIN_IN,
        *_vni_match(vni, dstport),
        "-m", "policy", "--dir", "in", "--pol", "none",
        "-j", "DROP",
    ]  # fmt: skip


def plaintext_drop_check_args(vni: int, dstport: int = VXLAN_DSTPORT) -> list[str]:
    return ["iptables", "-C", *_plaintext_drop_rule(vni, dstport)]


def plaintext_drop_add_args(vni: int, dstport: int = VXLAN_DSTPORT) -> list[str]:
    # Inserted, not appended. Inside a chain of our own the order is immaterial -- the rules are
    # disjoint by VNI -- but a restored rule has to outrank anything that displaced it: an
    # impostor carrying the same VNI with an ACCEPT would otherwise sit above the DROP that was
    # put back, and go on bypassing it.
    return ["iptables", "-I", *_plaintext_drop_rule(vni, dstport)]


def plaintext_drop_del_args(vni: int, dstport: int = VXLAN_DSTPORT) -> list[str]:
    return ["iptables", "-D", *_plaintext_drop_rule(vni, dstport)]


# --- fail-closed egress guard for an encrypted VNI ---
#
# The mark below is what selects the outbound XFRM policy, and MARK is not a terminating target:
# any later rule in the same hook can overwrite it, after which the policy no longer matches and
# the frame leaves in CLEAR TEXT with nothing reporting it. Measured in a pair of namespaces:
# with the mark rule removed, 8 of 8 VXLAN frames left unencrypted; with this guard installed,
# 0 left and 0 were encrypted -- the traffic stops instead of leaking. ``--dir out --pol none``
# is the exact question: by the time filter OUTPUT runs, the route's XFRM bundle is resolved, so
# "no policy" here means "this frame is about to go out in the clear".


def _egress_guard_rule(vni: int, dstport: int) -> list[str]:
    return [
        CHAIN_GUARD,
        *_vni_match(vni, dstport),
        "-m", "policy", "--dir", "out", "--pol", "none",
        "-j", "DROP",
    ]  # fmt: skip


def egress_guard_check_args(vni: int, dstport: int = VXLAN_DSTPORT) -> list[str]:
    return ["iptables", "-C", *_egress_guard_rule(vni, dstport)]


def egress_guard_add_args(vni: int, dstport: int = VXLAN_DSTPORT) -> list[str]:
    # Inserted, not appended. Inside a chain of our own the order is immaterial -- the rules are
    # disjoint by VNI -- but a restored rule has to outrank anything that displaced it: an
    # impostor carrying the same VNI with an ACCEPT would otherwise sit above the DROP that was
    # put back, and go on bypassing it.
    return ["iptables", "-I", *_egress_guard_rule(vni, dstport)]


def egress_guard_del_args(vni: int, dstport: int = VXLAN_DSTPORT) -> list[str]:
    return ["iptables", "-D", *_egress_guard_rule(vni, dstport)]


# --- mark outbound VXLAN for an encrypted VNI ---


def _output_mark_rule(vni: int, dstport: int) -> list[str]:
    return [
        CHAIN_MARK,
        *_vni_match(vni, dstport),
        "-j", "MARK", "--set-mark", f"{XFRM_MARK:#x}",
    ]  # fmt: skip


def output_mark_check_args(vni: int, dstport: int = VXLAN_DSTPORT) -> list[str]:
    return ["iptables", "-t", "mangle", "-C", *_output_mark_rule(vni, dstport)]


def output_mark_add_args(vni: int, dstport: int = VXLAN_DSTPORT) -> list[str]:
    # Inserted for the same reason as the filter rules above.
    return ["iptables", "-t", "mangle", "-I", *_output_mark_rule(vni, dstport)]


def output_mark_del_args(vni: int, dstport: int = VXLAN_DSTPORT) -> list[str]:
    return ["iptables", "-t", "mangle", "-D", *_output_mark_rule(vni, dstport)]


# --- pure CNI config assembly ---


def _overlay_ipam(meta: SessionNetMeta, ip: str) -> dict[str, Any]:
    """Static IPAM at the manager-assigned endpoint IP.

    The overlay subnet is stretched across every node in the session, so the address MUST come
    from the manager's central ``endpoints/`` table — which hands each endpoint a disjoint IP by
    construction. A per-node host-local pick would give every node the same first address and
    collide across the tunnel. There is no local fallback: this backend is multi-node only (the
    single-node path uses the bridge backend), and the manager assigns an endpoint IP to every
    kernel that has an agent, so a missing IP here is a control-plane bug, not a fallback case —
    the caller raises rather than silently attach a colliding address."""
    prefixlen = ipaddress.ip_network(meta.subnet).prefixlen
    return {"type": "static", "addresses": [{"address": f"{ip}/{prefixlen}"}]}


def overlay_cni_config(meta: SessionNetMeta, ip: str | None = None) -> dict[str, Any]:
    """CNI 'bridge' config attaching the container to this session's overlay bridge.

    ``ip`` is the manager-assigned overlay address and is required: without it the container
    cannot be given a cluster-unique address on the stretched overlay (see _overlay_ipam)."""
    if meta.vni is None:
        raise ValueError(f"overlay_cni_config requires a vxlan meta with a VNI: {meta}")
    if ip is None:
        raise OverlayAddressNotAssigned(
            f"no manager-assigned overlay IP for session {meta.session_id}; "
            "cannot attach to the stretched overlay without a cluster-unique address"
        )
    # The overlay NIC's MAC is pinned to the deterministic address the manager programs into every
    # peer's FDB/ARP (mac_for_ip) — otherwise the veth gets a random MAC and a peer's unicast frame
    # (dst=02:42:<ip>) arriving over the tunnel does not match the NIC and is dropped, breaking
    # cross-node overlay traffic. The pin is expressed in standard CNI vocabulary: the config
    # DECLARES the ``mac`` capability, and the value is supplied out-of-band as a capability arg
    # (overlay_mac_capability_args) that the provisioner injects into runtimeConfig — so a real CNI
    # ``bridge`` binary honours it, unlike the old non-standard top-level ``mac`` key it would drop.
    return {
        "cniVersion": "1.0.0",
        "name": f"bai-overlay-{meta.session_id}",
        "type": "bridge",
        "bridge": bridge_dev(meta.vni),
        "isGateway": False,
        "ipMasq": False,
        "mtu": meta.mtu,
        "ipam": _overlay_ipam(meta, ip),
        "capabilities": {"mac": True},
    }


def overlay_mac_capability_args(ip: str) -> dict[str, Any]:
    """The standard ``mac`` capability arg pinning the overlay NIC to its deterministic address
    (mac_for_ip), which every peer's FDB/ARP is programmed to."""
    return {"mac": mac_for_ip(ip)}


def local_bridge_dev(vni: int) -> str:
    return f"bailo{vni}"


def local_cni_config(
    session_id: str, *, bridge: str, subnet: str, static_ip: str | None = None
) -> dict[str, Any]:
    """CNI 'bridge' config for the host-local interface: agent<->container control
    channel plus egress NAT, carrying the default route.

    Per BEP-1062 Decision Log (2026-07-03): the LOCAL bridge is **per session**, on a
    **node-local** NAT subnet (not the stretched overlay subnet). Cross-session isolation
    comes from separate bridges (verified §8), not ICC-off firewall rules (the stock CNI
    bridge does not implement ICC-off — §9). A node-local subnet also avoids the
    stretched-L2 gateway conflict that folding egress into the overlay bridge would cause
    (option C, rejected in §9).

    ``static_ip`` pins the container at a specific address in the subnet (single-node cluster
    peers, so /etc/hosts resolves) while keeping host-local's pool + gateway + MASQ; None keeps
    the dynamic host-local pick for ordinary single-kernel sessions.

    The pin is expressed in standard CNI vocabulary: when ``static_ip`` is set the config DECLARES
    the ``ips`` capability, and the address is supplied out-of-band as a capability arg
    (local_ip_capability_args) that the provisioner injects into runtimeConfig. This replaces the
    old non-standard ``ipam.requested_ip`` key, which a real host-local binary would ignore —
    silently handing out a dynamic address and breaking the pin."""
    config: dict[str, Any] = {
        "cniVersion": "1.0.0",
        "name": f"bai-local-{session_id}",
        "type": "bridge",
        "bridge": bridge,
        "isGateway": True,
        "isDefaultGateway": True,
        "ipMasq": True,
        "hairpinMode": False,
        "ipam": {"type": "host-local", "subnet": subnet},
    }
    if static_ip is not None:
        config["capabilities"] = {"ips": True}
    return config


def local_ip_capability_args(subnet: str, static_ip: str) -> dict[str, Any]:
    """The standard ``ips`` capability arg pinning the LOCAL NIC to ``static_ip`` within ``subnet``
    (single-node cluster peers, so /etc/hosts resolves). CNI ``ips`` args are CIDR strings."""
    prefixlen = ipaddress.ip_network(subnet).prefixlen
    return {"ips": [f"{static_ip}/{prefixlen}"]}


#: Substrings that mean "the thing you asked me to remove is not here" rather than "I failed".
#: iproute2 and iptables both report this as a plain non-zero exit, so the text is the only signal.
_ABSENT_MARKERS: Final = (
    "does a matching rule exist",  # iptables -D, rule not present
    "no chain/target/match by that name",  # iptables -D/-X, chain not present
    "cannot find device",  # ip link del
    "no such process",  # ip xfrm state/policy del (ESRCH)
    "no such file or directory",  # bridge fdb del, ip neigh del
    "cannot delete",  # iptables -X on a chain that was never created
)


def is_absent_error(exc: BaseException) -> bool:
    """Whether a removal failed only because its target is already gone.

    Teardown treats exactly this as success. Everything else -- EPERM, a held xtables lock, EBUSY,
    an nft backend error -- is a real failure that leaves state on the host, and calling it success
    is what turns a retryable problem into a permanent leak.

    A missing binary is NOT absence. `ip` or `iptables` disappearing from PATH after the devices
    and rules were made says nothing about whether they are still there; it says this node can no
    longer clean up, which is a failure to report, not a teardown to record as done.
    """
    text = str(exc).lower()
    return any(marker in text for marker in _ABSENT_MARKERS)


async def _read_command(argv: Sequence[str]) -> str:
    """Run a command and return its stdout, or "" if it could not run.

    Only the firewall's own rule listing goes through here, and a listing that cannot be read is
    the same situation as one that shows drift: the caller re-asserts. So a failure is an empty
    listing rather than an exception.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
    except OSError:
        return ""
    return stdout.decode(errors="replace") if proc.returncode == 0 else ""


async def _run_command(argv: Sequence[str]) -> None:
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        display_argv = list(argv)
        secrets: set[str] = set()
        for index, value in enumerate(display_argv):
            # `ip xfrm state ... aead ALGORITHM KEY ICV_BITS`: the value two positions after
            # ``aead`` is the derived pair key plus RFC 4106 salt. It must not cross the
            # subprocess boundary a second time through logs or exception telemetry.
            if value == "aead" and index + 2 < len(display_argv):
                secrets.add(display_argv[index + 2])
                display_argv[index + 2] = "[REDACTED]"
        display_stderr = stderr.decode(errors="replace").strip()
        for secret in secrets:
            display_stderr = display_stderr.replace(secret, "[REDACTED]")
        raise RuntimeError(
            f"command failed (rc={proc.returncode}): {' '.join(display_argv)}: {display_stderr}"
        )


class VxlanNetworkPlugin(AbstractNetworkAgentPluginV2[AbstractKernel]):
    """VXLAN data-plane backend."""

    _runner: Runner
    _uplink: str
    _sessions: dict[str, SessionNetMeta]
    _self_vteps: dict[str, str]
    _local_subnets: LocalSubnetAllocator
    _mtu_probe: MtuProbe
    _reach_probe: ReachProbe
    _vxlan_lister: VxlanLister
    # Peers whose ESP SA/policy pair this node has programmed, per session. XFRM lives in the
    # netns rather than on the device, so teardown has to unprogram it explicitly and cannot rely
    # on `del_peer` having run for every peer first.
    _encrypted_peers: dict[str, set[str]]
    # Which sessions are carried by the ESP state+policy of a given (self VTEP, peer VTEP, port).
    # Both are node-pair resources: the policy selector is the outer packet and carries nothing per
    # session, and the SA ring it selects is now the pair's too (one cluster root and generation,
    # so there is nothing to tell apart). Tearing either down with whichever session ends first is
    # what broke the others
    # -- silently to clear text when it was the policy. Keyed by session id rather than counted so
    # add/remove stay idempotent under the coordinator's retries.
    _pair_users: dict[tuple[str, str, int], set[str]]
    #: The pairs the kernel actually holds an SA and policy for. Separate from ``_pair_users``,
    #: which records who would have to release a pair: a session is recorded as a user before the
    #: commands run (so a partial failure is still cleaned up), and treating that record as proof
    #: of programming would make every retry skip a pair that was never finished.
    _programmed_pairs: set[tuple[str, str, int]]
    # Per-session background reach probes, so teardown does not leave them running against a
    # bridge that is being deleted.
    _reach_tasks: dict[str, set[asyncio.Task[None]]]
    #: Per session, the peer VTEPs a probe is in flight for or has already had answered. The probe
    #: tests the tunnel to a node, not the endpoint at the far end of it, so one per peer says
    #: everything eight kernels behind that peer would say -- and says it with one task and one
    #: raw socket instead of eight. A probe that goes unanswered clears its entry, so the next
    #: endpoint behind that peer tries again: the first one may simply have been early.
    _reach_probed: dict[str, set[str]]
    #: Peers whose tunnel went unanswered, per session. Kept so the failure outlives the log line
    #: that reports it -- a session is left RUNNING on purpose here, and without this the only
    #: trace is in the agent's log while the user sees a rendezvous that never completes.
    _unreachable_peers: dict[str, set[str]]
    #: Per-session security state machines. They distinguish verification of a previously safe,
    #: open tunnel from restoration of a held-down one, so only the latter may raise the link after
    #: the complete peer set is protected.
    _security_states: dict[str, VxlanSecurityStateMachine]
    #: One lock per ESP pair, held across the refcount decision AND the kernel commands that follow
    #: from it. The SA and policy are shared by every session between the same two nodes on the same
    #: port, so two sessions racing on one pair can interleave into "A decides it is the last user,
    #: B programs the pair, A deletes what B just made" -- B then holds an open FDB with nothing
    #: encrypting it. Per pair, not global: unrelated pairs have no reason to wait on each other.
    _pair_locks: dict[tuple[str, str, int], asyncio.Lock]
    #: Full generation currently stored in each of a pair's three SPI slots. The SPI is bounded by
    #: slot, while the key derivation includes the full generation; this map tells rotation which
    #: stale slot must be deleted and recreated rather than incorrectly `update`d in place.
    _pair_slot_generations: dict[tuple[str, str, int], dict[int, int]]
    #: The outbound generation never moves backwards if wall clock is corrected. A rollback would
    #: deliberately resume a retired traffic key and reset this process's security horizon.
    _pair_active_generations: dict[tuple[str, str, int], int]
    _key_generation: KeyGeneration
    #: Serialize forwarding changes for one session/VTEP. Without this, DEL_PEER can observe no
    #: endpoint yet, remove the pair, and race with ADD_ENDPOINT opening a unicast FDB immediately
    #: afterwards.
    _forwarding_locks: dict[tuple[str, str], asyncio.Lock]
    #: Remote endpoint FDB entries known to this process. DEL_PEER refuses to withdraw XFRM while
    #: any remain; the coordinator orders endpoint withdrawal before peer withdrawal as the
    #: durable/restart-safe half of the same invariant.
    _remote_endpoints: dict[str, dict[tuple[str, str], str]]
    #: Reads the firewall's own rule order, so reconcile can restore it (see `jump_is_first`).
    _reader: Reader
    #: Serialises a session's teardown against the protection watchdog. Without it the watchdog
    #: can read the host state, have the session torn down under it while it awaits, and then
    #: reinstall the dead session's rules, XFRM and pair claim -- which the next session to draw
    #: that VNI inherits.
    _session_guards: dict[str, asyncio.Lock]
    #: The node's single protection watchdog. One task, not one per session.
    _protection_task: asyncio.Task[None] | None
    #: Node-wide record of who is using each ESP pair. The in-process refcount below is only
    #: node-wide where one privnet owns the host; with the backend in-process, every agent has
    #: its own and each believes it is the pair's sole user.
    _pair_journal: PairJournal
    #: This node's name for the claims it makes in that journal. The AGENT ID, not a pid: claims
    #: outlive the process, and an owner that changed on every restart would strand each of them
    #: on a pair nobody then removes. Same convention as the node-local subnet journal.
    _journal_owner: str
    #: Surviving tunnels `prepare_recovery` could not bring down. Kept because the privnet
    #: continues in degraded mode after that failure, and a device nothing can classify is
    #: an open path: setup refuses the VNI that names one until it is actually closed.
    _unclosed_devices: set[str]

    def __init__(
        self,
        plugin_config: Any,
        local_config: Any,
        *,
        uplink: str = "eth0",
        runner: Runner | None = None,
        reader: Reader | None = None,
        local_subnets: LocalSubnetAllocator | None = None,
        pair_journal: PairJournal | None = None,
        journal_owner: str | None = None,
        mtu_probe: MtuProbe | None = None,
        reach_probe: ReachProbe | None = None,
        vxlan_lister: VxlanLister | None = None,
        key_generation: KeyGeneration | None = None,
    ) -> None:
        super().__init__(plugin_config, local_config)
        self._uplink = uplink
        self._runner = runner or _run_command
        self._reader = reader or _read_command
        self._unclosed_devices = set()
        self._protection_task = None
        self._session_guards = {}
        self._pair_journal = pair_journal or PairJournal()
        # A pid only as the last resort: it is wrong across restarts, but a claim tagged
        # with something is still better than one that cannot be told from a peer's.
        self._journal_owner = journal_owner or f"pid{os.getpid()}"
        # Injectable for the same reason as `runner`: the probe shells out and reads sysfs, and the
        # command builders must stay testable without either.
        self._mtu_probe = mtu_probe or underlay_mtu
        self._reach_probe = reach_probe or arp_probe
        self._vxlan_lister = vxlan_lister or _list_vxlan_devices
        self._key_generation = key_generation or (
            lambda: int(time.time() // KEY_ROTATION_INTERVAL_SEC)
        )
        self._reach_tasks = {}
        self._reach_probed = {}
        self._unreachable_peers = {}
        self._encrypted_peers = {}
        self._pair_users = {}
        self._programmed_pairs = set()
        self._security_states = {}
        self._pair_locks = {}
        self._pair_slot_generations = {}
        self._pair_active_generations = {}
        self._forwarding_locks = {}
        self._remote_endpoints = {}
        self._sessions = {}
        # This node's own VXLAN tunnel endpoint per session — the local `src` for every XFRM SA,
        # captured from `self_member` at setup/adopt because add_peer/del_peer only receive the peer.
        self._self_vteps = {}
        # Defaults to the store's single process-wide owner, which is also what the bridge backend
        # resolves: both carve their LOCAL block out of the same node-local pool, so one owner keeps
        # their indices from colliding on a subnet.
        self._local_subnets = local_subnets or get_local_subnet_allocator()

    async def _local_index(self, session_id: str) -> int:
        """The session's node-local block index (idempotent, durable across restarts).

        The LOCAL bridge is named after this, not after the VNI. `local_subnet` documents the
        index as naming BOTH the device `bailo<index>` and the subnet its gateway sits on, and the
        node-wide store's whole job is to keep two agents from deriving the same one. Naming the
        device off the VNI instead took the device out of that guarantee and left the two halves
        keyed on unrelated numbers -- safe only for as long as the VNI range (4096+) stays clear of
        the index range (0..pool size), which is a configuration away from not being true.
        """
        return await self._local_subnets.allocate(session_id)

    async def _local_subnet(self, session_id: str) -> str:
        """The node-local block for the session's LOCAL/egress bridge (idempotent, durable).

        Node-local (behind NAT, never stretched across nodes), so it needs no cross-node
        coordination and cannot collide with another node's LOCAL subnet. The pool it is cut from
        and the size of the cut are the operator's (`container.local-network-*`).
        """
        return await self._local_subnets.allocate_subnet(session_id)

    @override
    async def init(self, context: Any = None) -> None:
        # The chains are host-global and shared by every encrypted session, so they are built
        # once here rather than by whichever session happens to be first. Best-effort: a node
        # that cannot make them refuses the session that needs them (`_ensure_plaintext_drop`),
        # which is where that failure belongs.
        try:
            await self._ensure_owned_chains()
        except Exception:
            log.warning(
                "could not install the overlay firewall chains at startup; an encrypted session"
                " scheduled here will retry and refuse if it still cannot",
                exc_info=True,
            )
        # ONE watchdog for the node, not one per session. What it costs does not grow with the
        # session count, which is what lets it run often enough to matter.
        if self._protection_task is None or self._protection_task.done():
            self._protection_task = asyncio.create_task(self._protection_watchdog())

    async def _protection_watchdog(self) -> None:
        """Re-assert every encrypted session's protection on one node-wide clock."""
        while True:
            try:
                await self.reassert_protection()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("the overlay protection watchdog pass failed")
            await asyncio.sleep(PROTECTION_INTERVAL_SEC)

    @override
    async def cleanup(self) -> None:
        if self._protection_task is not None:
            self._protection_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._protection_task
            self._protection_task = None
        await self._remove_owned_chains()

    @override
    async def update_plugin_config(self, plugin_config: Any) -> None:
        self.plugin_config = plugin_config

    @override
    async def probe_caps(self) -> AgentNetworkCaps:
        return await probe_caps(self._uplink)

    async def _measured_overlay_ceiling(self, meta: SessionNetMeta) -> int | None:
        """The largest overlay MTU this node's underlay can actually carry, or None if unmeasurable."""
        underlay = await self._mtu_probe(self._uplink)
        if underlay is None:
            return None
        return underlay - VXLAN_OVERHEAD - (ESP_OVERHEAD if meta.encryption_key else 0)

    async def _require_mtu_fits(self, meta: SessionNetMeta) -> None:
        """Refuse the session when the manager's overlay MTU exceeds this node's real underlay.

        The manager derives the number from a configured constant; only the node can tell what its
        pod network really leaves. When they disagree the overlay still comes up and still passes
        small packets, so nothing surfaces until a bulk transfer hangs. See path_mtu.py for the
        measured per-CNI numbers.
        """
        ceiling = await self._measured_overlay_ceiling(meta)
        if ceiling is None:
            log.warning(
                "could not measure the underlay MTU on {}; accepting the manager's overlay MTU "
                "{} unchecked",
                self._uplink,
                meta.mtu,
            )
            return
        if meta.mtu > ceiling:
            raise OverlayMtuTooLarge(
                f"session {meta.session_id}: overlay MTU {meta.mtu} exceeds what uplink "
                f"{self._uplink} can carry ({ceiling}). The pod network on this node encapsulates, "
                f"so the manager's assumed underlay is {meta.mtu - ceiling} bytes too large. "
                f"Set the manager's network plugin `mtu` to this node's measured underlay "
                f"({ceiling + VXLAN_OVERHEAD + (ESP_OVERHEAD if meta.encryption_key else 0)})."
            )

    async def _delete_link_quiet(self, dev: str) -> None:
        """Delete a link if present; ignore 'does not exist' failures."""
        try:
            await self._runner(link_del_args(dev))
        except RuntimeError:
            pass

    async def _hold_vxlan_down_or_absent(self, dev: str) -> bool:
        """Return whether this VXLAN can no longer carry traffic.

        `ip link set ... down` reports an error when a link disappears between discovery and the
        command. That is already the state teardown/recovery needs. A second inventory check makes
        that race idempotent without treating a live link's permission or netlink error as safe.
        """
        try:
            await self._runner(link_down_args(dev))
            return True
        except (RuntimeError, OSError) as down_error:
            try:
                devices = await self._vxlan_lister()
            except Exception as inventory_error:
                log.warning(
                    "could not verify whether {} disappeared after link-down failed: {}; "
                    "inventory failed: {}",
                    dev,
                    down_error,
                    inventory_error,
                )
                return False
            if dev not in devices:
                log.debug("{} disappeared before link-down completed; treating it as closed", dev)
                return True
            log.warning("could not bring surviving VXLAN {} down: {}", dev, down_error)
            return False

    async def _ensure_forward_accept(self, vni: int) -> None:
        """Idempotently accept intra-bridge forwarding on the overlay bridge, so a DROP FORWARD
        policy (br_netfilter + a Docker/hardened host) cannot silently kill the overlay. Best-effort:
        harmless where FORWARD already accepts, and a host without iptables has no such policy."""
        try:
            await self._runner(forward_accept_check_args(vni))
            return  # already present
        except (RuntimeError, OSError):
            pass  # absent, or iptables unavailable -- try to add it
        try:
            await self._runner(forward_accept_add_args(vni))
        except (RuntimeError, OSError) as e:
            log.warning("could not install overlay FORWARD-ACCEPT for {}: {}", bridge_dev(vni), e)

    async def _del_forward_accept(self, vni: int, failures: list[str] | None = None) -> None:
        await self._remove(forward_accept_del_args(vni), failures)

    async def _remove(self, argv: Sequence[str], failures: list[str] | None = None) -> None:
        """Run one removal command, treating "already gone" as done.

        With ``failures`` the caller is collecting and decides afterwards; without it a real
        failure propagates. Either way it is never silently discarded, which is what let a
        permission error or a held xtables lock be reported as a completed teardown.
        """
        try:
            await self._runner(argv)
        except (RuntimeError, OSError) as e:
            if is_absent_error(e):
                return
            if failures is None:
                raise
            failures.append(f"{' '.join(argv[:5])}: {e}")

    def _session_guard(self, session_id: str) -> asyncio.Lock:
        return self._session_guards.setdefault(session_id, asyncio.Lock())

    async def _snapshot_protection(self) -> ProtectionSnapshot:
        """Read the node's whole protection state once, for the periodic re-assert."""
        return ProtectionSnapshot(
            filter_rules=await self._reader(["iptables-save", "-t", "filter"]),
            mangle_rules=await self._reader(["iptables-save", "-t", "mangle"]),
            sa_endpoints=parse_owned_sa_endpoints(
                await self._reader(["ip", "xfrm", "state"]), XFRM_REQID
            ),
            policy_pairs=parse_owned_policies(
                await self._reader(["ip", "xfrm", "policy"]), _XFRM_MARK
            ),
            up_devices=parse_up_vxlan_devices(
                await self._reader(["ip", "-o", "link", "show", "type", "vxlan"])
            ),
        )

    def _pair_intact(self, snapshot: ProtectionSnapshot, key: tuple[str, str, int]) -> bool:
        """Whether the kernel still holds everything this pair is supposed to have."""
        self_vtep, peer_vtep, dstport = key
        generations = self._pair_slot_generations.get(key)
        if not generations:
            return False
        for generation in generations.values():
            for src, dst in ((self_vtep, peer_vtep), (peer_vtep, self_vtep)):
                if (src, dst, _esp_spi(src, dst, generation)) not in snapshot.sa_endpoints:
                    return False
        return (self_vtep, peer_vtep, dstport) in snapshot.policy_pairs

    async def reassert_protection(self) -> None:
        """One node-wide pass: read the real state, change only what actually drifted.

        This replaces a per-session timer that reprogrammed everything unconditionally. Reading
        first is what makes it affordable -- four commands for the whole node instead of tens per
        session -- and it is also what makes it correct at scale: the old pass's own xtables lock
        contention was reported as a protection failure, which took down tunnels that were fine.
        """
        # (session, meta, vni) so the VNI is narrowed once here rather than re-proved below.
        encrypted = [
            (session_id, meta, meta.vni)
            for session_id, meta in self._sessions.items()
            if meta.encryption_key is not None and meta.vni is not None
        ]
        if not encrypted:
            return
        try:
            snapshot = await self._snapshot_protection()
        except Exception:
            log.exception("could not read this node's protection state; skipping this pass")
            return
        for table, builtin, chain in OWNED_CHAINS:
            if not jump_is_first(snapshot.table(table), builtin, chain):
                await self._ensure_owned_chains()
                break
        for session_id, meta, vni in encrypted:
            try:
                async with self._session_guard(session_id):
                    if self._sessions.get(session_id) is not meta:
                        # Torn down (or replaced) while this pass was reading. Reinstalling now
                        # would leave a dead session's rules and claim for the next session that
                        # draws this VNI to inherit.
                        continue
                    await self._reassert_session(session_id, meta, vni, snapshot)
            except Exception:
                # `_reassert_session` has already closed the tunnel for anything it could not
                # restore; one session's failure must not stop the rest of the node's.
                log.exception("could not re-assert protection for session {}", session_id)

    async def _reassert_session(
        self, session_id: str, meta: SessionNetMeta, vni: int, snapshot: ProtectionSnapshot
    ) -> None:
        machine = self._security_states.get(session_id)
        if machine is not None and machine.state is VxlanSecurityState.BLOCKING:
            # A prior link-down failed. Protection must not be rebuilt on top of an unconfirmed
            # open path and then mistaken for a normal restore: retry the physical block first.
            await self._close_tunnel(
                meta,
                session_id,
                machine.failure_reason or "the overlay tunnel has not been confirmed down",
            )
            if machine.state is VxlanSecurityState.BLOCKING:
                return  # still not down; the next pass tries again
        # Moves a BLOCKED session to RESTORING, which is what lets `_reopen_tunnel` below raise
        # the link once everything checks out. Without it a fail-closed session stays closed no
        # matter how many times its protection is found intact.
        self._transition_security(session_id, VxlanSecurityEvent.RECONCILE_STARTED)
        # The whole rule, as this backend builds it -- not just "something mentions this VNI".
        # A rule with the wrong port, the wrong policy direction, or an ACCEPT where the DROP
        # belongs would otherwise be read as protection.
        missing = [
            name
            for name, table, expected in (
                ("drop", "filter", _plaintext_drop_rule(vni, meta.vxlan_port)),
                ("guard", "filter", _egress_guard_rule(vni, meta.vxlan_port)),
                ("mark", "mangle", _output_mark_rule(vni, meta.vxlan_port)),
            )
            if not rule_is_present(snapshot.table(table), expected)
        ]
        if missing:
            # Only the rules that are actually gone, and only for this VNI.
            if not await self._firewall_side_ok(meta, session_id):
                raise OverlayEncryptionUnavailable(
                    f"session {session_id} is encrypted but its {', '.join(missing)} rule(s) could"
                    " not be restored; the overlay tunnel is held down until they can"
                )
        self_vtep = self._self_vteps.get(session_id)
        if self_vtep is None:
            return
        generation = self._key_generation()
        for peer_vtep in sorted(self._encrypted_peers.get(session_id, set())):
            key = (self_vtep, peer_vtep, meta.vxlan_port)
            # `force` only for kernel state that is actually gone. A pair whose generation has
            # merely moved on is reprogrammed the ordinary way -- which is also the ONLY thing
            # that drives the 12-hour key rotation now that a steady membership no longer calls
            # `ensure_session_security`: nothing else asks what generation it should be on, so
            # the pairs would sit on their first one for the life of the session.
            drifted = not self._pair_intact(snapshot, key)
            rotated = self._pair_active_generations.get(key, generation) < generation
            if not drifted and not rotated:
                continue  # the kernel has it, at the generation it should be on
            try:
                if not await self._program_encryption(meta, session_id, peer_vtep, force=drifted):
                    raise OverlayEncryptionUnavailable(
                        f"session {session_id} cannot re-assert the ESP pair for {peer_vtep}"
                    )
            except Exception:
                # The FDB entry for this peer is already open, so a failure here is not "the peer
                # is unreachable" but "the peer is reachable and may be unprotected".
                self._forget_pair(meta, session_id, peer_vtep)
                await self._close_tunnel(
                    meta, session_id, f"the ESP pair for {peer_vtep} could not be re-asserted"
                )
                raise
        # Everything this session needs is in place, so a tunnel held down because it once was
        # not may come back. Without this a single failed pass closed the session for good: the
        # only other caller of `_reopen_tunnel` is `ensure_session_security`, which a steady
        # membership no longer reaches.
        if not await self._reopen_tunnel(meta, session_id):
            raise OverlayEncryptionUnavailable(
                f"session {session_id}'s protection was restored but its overlay tunnel could"
                " not be reopened"
            )
        if (
            vxlan_dev(vni) not in snapshot.up_devices
            and (machine := self._security_states.get(session_id)) is not None
            and machine.state in {VxlanSecurityState.READY, VxlanSecurityState.PLAINTEXT}
        ):
            # Down while this node believes it is carrying: a co-located agent restarted and its
            # fail-close preflight downs every `baivx*` on the host, ours included. Nothing else
            # looks -- the membership did not change and this session's own state still says
            # READY -- so the device stays down for the life of the process.
            log.warning(
                "{} was down while session {} is READY; raising it again",
                vxlan_dev(vni),
                session_id,
            )
            await self._runner(link_up_args(vxlan_dev(vni)))

    async def _ensure_owned_chains(self) -> None:
        """Create this backend's chains and put their jumps back at the head of the built-ins.

        Re-asserted on every protection check rather than only at setup: the jump is host state,
        and a co-tenant that inserts its own rule at position 1 leaves ours present but
        unreachable. `iptables -C` cannot see that, which is why this reads the listing.
        """
        for table, builtin, chain in OWNED_CHAINS:
            try:
                await self._runner(chain_create_args(table, chain))
            except (RuntimeError, OSError):
                pass  # already exists
            listing = await self._reader(chain_list_args(table, builtin))
            if jump_is_first(listing, builtin, chain):
                continue
            # Not first: it is either missing or has been displaced. Drop any existing copy
            # before re-inserting, so a displaced jump does not become a duplicate.
            try:
                await self._runner(jump_del_args(table, builtin, chain))
            except (RuntimeError, OSError):
                pass  # nothing to remove
            await self._runner(jump_add_args(table, builtin, chain))

    async def _remove_owned_chains(self) -> None:
        """Withdraw the chains. Only at process cleanup -- never while a session ends.

        They are host-global and every encrypted session's rules live in them, but the only
        record of who needs them is this process's `_sessions`, which a session joins AFTER its
        rules are installed. A teardown that consulted it could therefore look during that gap,
        conclude nobody is left, and delete the chains out from under a session that had just
        finished protecting itself -- leaving it sending and accepting clear text until the next
        reconcile. An empty chain costs nothing; that window costs the guarantee.
        """
        for table, builtin, chain in OWNED_CHAINS:
            for argv in (
                jump_del_args(table, builtin, chain),
                chain_flush_args(table, chain),
                chain_delete_args(table, chain),
            ):
                try:
                    await self._runner(argv)
                except (RuntimeError, OSError):
                    pass  # never installed, or already gone

    async def _ensure_rule(self, check: Sequence[str], add: Sequence[str]) -> None:
        try:
            await self._runner(check)
            return  # already present
        except (RuntimeError, OSError):
            pass  # absent, or a match module is unavailable -- try to add it
        await self._runner(add)

    async def _ensure_plaintext_drop(self, vni: int, dstport: int) -> None:
        """Close the receive side of an encrypted VNI: drop VXLAN that did not arrive inside an SA.

        Not best-effort, unlike the FORWARD accept above. A missing accept costs connectivity and
        says so loudly; a missing drop costs the guarantee the session was created under, silently
        -- the overlay comes up, carries traffic, and takes anyone's plaintext along with it. The
        caller turns a failure here into a refusal to start the session.
        """
        try:
            await self._ensure_owned_chains()
            await self._ensure_rule(
                plaintext_drop_check_args(vni, dstport),
                plaintext_drop_add_args(vni, dstport),
            )
        except (RuntimeError, OSError) as e:
            raise OverlayEncryptionUnavailable(
                f"could not install the plaintext-drop rule for encrypted VNI {vni} on udp/"
                f"{dstport}: {e}. Without it the overlay accepts injected clear-text frames on "
                "this node, so the session is refused rather than run under a guarantee it does "
                "not have. The rule needs the iptables `u32` and `policy` matches "
                "(xt_u32, xt_policy)."
            ) from e

    async def _del_plaintext_drop(
        self, vni: int, dstport: int, failures: list[str] | None = None
    ) -> None:
        await self._remove(plaintext_drop_del_args(vni, dstport), failures)

    async def _ensure_egress_guard(self, vni: int, dstport: int) -> None:
        """Refuse to emit this VNI's VXLAN unencrypted, whatever happened to the mark.

        The mark alone is fail-OPEN: MARK is not terminating, so a later rule in the same hook
        can clear it and the frame leaves in clear text. This turns that into fail-CLOSED --
        the packet is dropped and the session goes visibly dead instead of quietly plain.
        """
        try:
            await self._ensure_owned_chains()
            await self._ensure_rule(
                egress_guard_check_args(vni, dstport),
                egress_guard_add_args(vni, dstport),
            )
        except (RuntimeError, OSError) as e:
            raise OverlayEncryptionUnavailable(
                f"could not install the egress guard for encrypted VNI {vni} on udp/{dstport}: "
                f"{e}. Without it, anything that clears the OUTPUT mark sends this session's "
                "traffic in clear text with nothing reporting it."
            ) from e

    async def _del_egress_guard(
        self, vni: int, dstport: int, failures: list[str] | None = None
    ) -> None:
        await self._remove(egress_guard_del_args(vni, dstport), failures)

    async def _ensure_output_mark(self, vni: int, dstport: int) -> None:
        """Mark only this encrypted VNI for the outbound XFRM policy."""
        try:
            await self._ensure_owned_chains()
            await self._ensure_rule(
                output_mark_check_args(vni, dstport),
                output_mark_add_args(vni, dstport),
            )
        except (RuntimeError, OSError) as e:
            raise OverlayEncryptionUnavailable(
                f"could not install the OUTPUT mark for encrypted VNI {vni} on udp/{dstport}: "
                f"{e}. Without it the VNI-scoped XFRM policy cannot select outgoing packets, so "
                "the session is refused instead of transmitting in clear text."
            ) from e

    async def _del_output_mark(
        self, vni: int, dstport: int, failures: list[str] | None = None
    ) -> None:
        await self._remove(output_mark_del_args(vni, dstport), failures)

    def security_state(self, session_id: str) -> VxlanSecurityState | None:
        """Return this node's current VXLAN protection state for diagnostics."""
        machine = self._security_states.get(session_id)
        return None if machine is None else machine.state

    def _register_security_state(self, meta: SessionNetMeta) -> None:
        initial = (
            VxlanSecurityState.PLAINTEXT
            if meta.encryption_key is None
            else VxlanSecurityState.READY
        )
        self._security_states[meta.session_id] = VxlanSecurityStateMachine(initial)

    def _transition_security(
        self,
        session_id: str,
        event: VxlanSecurityEvent,
        *,
        reason: str | None = None,
    ) -> VxlanSecurityState | None:
        machine = self._security_states.get(session_id)
        if machine is None:
            return None
        previous = machine.state
        current = machine.transition(event, reason=reason)
        if current is not previous:
            log.debug(
                "vxlan security state for session {}: {} -> {} ({})",
                session_id,
                previous,
                current,
                event,
            )
        return current

    async def _firewall_side_ok(self, meta: SessionNetMeta, session_id: str) -> bool:
        """Whether this encrypted VNI's inbound drop, outbound mark and egress guard are in place.

        setup refuses a session it cannot protect, so this exists for the session that was already
        running: iptables is host state, and a firewall reload or an `iptables -F` between two
        agent lives leaves the devices up and encrypted with the receive side wide open again.
        Adopting such a session and merely logging it is the same fail-open the drop rule was added
        to close, so the vxlan device is held DOWN instead -- the containers keep running and their
        node-local traffic with them, while nothing crosses the tunnel in either direction.

        This only validates protection. It deliberately does not raise a held-down device: the
        caller that owns the complete published peer set must restore every XFRM pair first.
        """
        if meta.encryption_key is None or meta.vni is None:
            return True
        try:
            await self._ensure_output_mark(meta.vni, meta.vxlan_port)
            await self._ensure_egress_guard(meta.vni, meta.vxlan_port)
            await self._ensure_plaintext_drop(meta.vni, meta.vxlan_port)
        except OverlayEncryptionUnavailable as e:
            await self._close_tunnel(meta, session_id, str(e))
            return False
        return True

    async def _reopen_tunnel(self, meta: SessionNetMeta, session_id: str) -> bool:
        """Raise a tunnel only after its receive rule and every published XFRM pair are ready."""
        machine = self._security_states.get(session_id)
        if machine is None:
            return False
        if machine.state in {VxlanSecurityState.PLAINTEXT, VxlanSecurityState.READY}:
            return True
        if machine.state is VxlanSecurityState.VERIFYING:
            self._transition_security(session_id, VxlanSecurityEvent.PROTECTION_READY)
            return True
        if machine.state is not VxlanSecurityState.RESTORING or meta.vni is None:
            return False
        # Raise the link while the machine still says RESTORING, and transition to READY only if
        # that worked. Transitioning first and then failing to raise the device would lose the one
        # record that says this session is still closed, so no later pass would retry it.
        try:
            await self._runner(link_up_args(vxlan_dev(meta.vni)))
        except (RuntimeError, OSError):
            self._transition_security(
                session_id,
                VxlanSecurityEvent.PROTECTION_FAILED,
                reason=f"{vxlan_dev(meta.vni)} could not be raised",
            )
            log.warning(
                "security state is back for session {} but {} could not be raised; keeping the "
                "tunnel closed so the next pass retries",
                session_id,
                vxlan_dev(meta.vni),
            )
            return False
        self._transition_security(session_id, VxlanSecurityEvent.PROTECTION_READY)
        log.info("security state is back for session {}; reopening the tunnel", session_id)
        return True

    def _pair_lock(self, key: tuple[str, str, int]) -> asyncio.Lock:
        return self._pair_locks.setdefault(key, asyncio.Lock())

    def _forwarding_lock(self, session_id: str, peer_vtep: str) -> asyncio.Lock:
        return self._forwarding_locks.setdefault((session_id, peer_vtep), asyncio.Lock())

    async def _close_tunnel(self, meta: SessionNetMeta, session_id: str, why: str) -> None:
        """Hold this session's tunnel down until something can protect it again.

        Shared by the two ways protection is lost -- the drop rule and the ESP pairs -- so both
        recover only after `ensure_session_security` has restored the complete peer set.
        """
        if meta.encryption_key is None or meta.vni is None:
            return
        machine = self._security_states.get(session_id)
        if machine is None:
            machine = VxlanSecurityStateMachine(VxlanSecurityState.READY)
            self._security_states[session_id] = machine
        was_confirmed_down = machine.holds_tunnel_down
        self._transition_security(session_id, VxlanSecurityEvent.PROTECTION_FAILED, reason=why)
        if was_confirmed_down:
            return
        log.error("closing the overlay tunnel for encrypted session {}: {}", session_id, why)
        if not await self._hold_vxlan_down_or_absent(vxlan_dev(meta.vni)):
            # Stay in BLOCKING. Calling this state BLOCKED would claim a physical invariant the
            # kernel command did not establish, and a later reconcile would then skip the only
            # operation that can close the clear-text path.
            log.warning(
                "could not bring {} down; the session remains BLOCKING and will retry",
                vxlan_dev(meta.vni),
            )
            return
        self._transition_security(session_id, VxlanSecurityEvent.TUNNEL_BLOCKED)

    def _forget_pair(self, meta: SessionNetMeta, session_id: str, peer_vtep: str) -> None:
        """Drop this pair's record of having been programmed, so nothing downstream trusts it.

        `_pair_is_protected` answers from `_programmed_pairs`, and a new endpoint would otherwise
        be given an FDB entry on the strength of a success that the kernel no longer reflects.
        """
        self_vtep = self._self_vteps.get(session_id)
        if self_vtep is None:
            return
        self._programmed_pairs.discard((self_vtep, peer_vtep, meta.vxlan_port))

    def _pair_is_protected(self, meta: SessionNetMeta, session_id: str, peer_vtep: str) -> bool:
        """Whether traffic to ``peer_vtep`` would actually be encrypted."""
        if meta.encryption_key is None:
            return True
        self_vtep = self._self_vteps.get(session_id)
        if self_vtep is None:
            return False
        if self_vtep == peer_vtep:
            return True  # this node's own endpoint: reached over the bridge, no tunnel involved
        return (self_vtep, peer_vtep, meta.vxlan_port) in self._programmed_pairs

    @override
    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        if meta.backend is not NetworkBackendKind.VXLAN or meta.vni is None:
            raise ValueError(f"VxlanNetworkPlugin requires a vxlan meta with a VNI: {meta}")
        vni = meta.vni
        # Preconditions, so they run before any side effect: a session this node cannot carry must
        # leave nothing half-built behind.
        await self._require_mtu_fits(meta)
        await self._require_closed(vni)
        await self._require_no_conflict(vni, meta.vxlan_port)
        if meta.encryption_key is not None and self_member.vtep_ip is None:
            # The SAs are keyed on the ordered VTEP pair, so with no local endpoint there is no
            # `src` to program them with. This used to warn from `add_peer` and carry on, which
            # brought the session up in clear text with nothing but a log line saying so.
            raise OverlayEncryptionUnavailable(
                f"session {meta.session_id} asks for an encrypted overlay, but this node has no "
                "usable VTEP address to anchor the ESP SAs on; refusing rather than running the "
                "session unencrypted"
            )
        # Leftover-safe: a stale device from a crashed/uncleaned prior session would make
        # `ip link add` fail with 'File exists' (and could carry stale FDB/IP). Delete any
        # pre-existing devices of these names first so setup always yields a fresh device.
        # The LOCAL bridge (bailo{vni}) is created later by CNI, but a leftover one keyed by
        # the (reused) vni retains a prior session's gateway IP and makes CNI ADD fail with
        # "already has an IP address different from ..." — so clear it here too.
        await self._delete_link_quiet(bridge_dev(vni))
        await self._delete_link_quiet(vxlan_dev(vni))
        await self._delete_link_quiet(local_bridge_dev(await self._local_index(meta.session_id)))
        # Transitional: sessions created before the LOCAL bridge was named after the index carry a
        # `bailo<vni>` device instead. An agent upgraded under them would otherwise never remove it.
        await self._delete_link_quiet(local_bridge_dev(vni))
        # The overlay MTU (underlay - VXLAN overhead) the manager put in the meta, applied to both
        # the vxlan device and the overlay bridge so a full-size inner frame fits the tunnel.
        # All of it or none of it. A failure partway used to leave a half-built vxlan or bridge
        # behind, and teardown skips a session it has no meta for -- so the device outlived every
        # record of it, and the next session that drew the same VNI (the manager hands them back)
        # inherited a stranger's device. Undo what landed and let the caller see the failure.
        try:
            await self._runner(
                vxlan_link_add_args(
                    vni,
                    self._uplink,
                    # The address this node published to its peers, not whatever the route table
                    # would pick — see vxlan_link_add_args.
                    local=self_member.vtep_ip,
                    mtu=meta.mtu,
                    dstport=meta.vxlan_port,
                )
            )
            await self._runner(bridge_link_add_args(vni, mtu=meta.mtu))
            await self._runner(set_master_args(vni))
            await self._runner(link_up_args(vxlan_dev(vni)))
            await self._runner(link_up_args(bridge_dev(vni)))
        except Exception:
            for dev in (bridge_dev(vni), vxlan_dev(vni)):
                await self._delete_link_quiet(dev)
            raise
        await self._ensure_forward_accept(vni)
        if meta.encryption_key is not None:
            try:
                await self._ensure_output_mark(vni, meta.vxlan_port)
                # The guard before the drop: from here on, a lost mark stops the traffic instead
                # of sending it in clear text.
                await self._ensure_egress_guard(vni, meta.vxlan_port)
                await self._ensure_plaintext_drop(vni, meta.vxlan_port)
            except Exception:
                rollback: list[str] = []
                await self._del_output_mark(vni, meta.vxlan_port, rollback)
                await self._del_egress_guard(vni, meta.vxlan_port, rollback)
                await self._del_forward_accept(vni, rollback)
                for dev in (bridge_dev(vni), vxlan_dev(vni)):
                    await self._delete_link_quiet(dev)
                raise
        self._sessions[meta.session_id] = meta
        self._register_security_state(meta)
        if self_member.vtep_ip is not None:
            self._self_vteps[meta.session_id] = self_member.vtep_ip

    def encrypted_peers(self, session_id: str) -> frozenset[str]:
        """The peer VTEPs this node still holds ESP state for, in this session.

        Also what a failed teardown must leave behind: it is the list the retry reads to find the
        pairs it still has to remove.
        """
        return frozenset(self._encrypted_peers.get(session_id, set()))

    def unreachable_peers(self, session_id: str) -> frozenset[str]:
        """The peer VTEPs whose tunnel went unanswered for this session, so far.

        The session is deliberately left RUNNING when a probe fails -- refusing one that was merely
        early is worse than the silence it replaces -- but "deliberately not fatal" is not the same
        as "not worth reporting". Empty is the healthy answer, and it is also the answer on a node
        whose kernel has no AF_PACKET: the probe cannot run there and says nothing either way.
        """
        return frozenset(self._unreachable_peers.get(session_id, set()))

    @override
    async def adopt_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        if meta.backend is not NetworkBackendKind.VXLAN or meta.vni is None:
            raise ValueError(f"VxlanNetworkPlugin requires a vxlan meta with a VNI: {meta}")
        # Register first so a tunnel held down below remains tearable. For encryption, close the
        # data path before any diagnostic await: a new process cannot know whether the surviving
        # XFRM set is complete, so even an MTU probe must not extend a possible clear-text window.
        self._sessions[meta.session_id] = meta
        self._register_security_state(meta)
        if self_member.vtep_ip is not None:
            self._self_vteps[meta.session_id] = self_member.vtep_ip
        if meta.encryption_key is not None:
            await self._close_tunnel(
                meta,
                meta.session_id,
                "the complete ESP peer set has not yet been re-asserted after adoption",
            )
            await self._firewall_side_ok(meta, meta.session_id)

        # Warn, do not refuse: unlike setup, the devices here are already up and carrying traffic,
        # and an agent restart that lands after the pod network changed under it would otherwise
        # kill sessions that are running. The operator still gets the number to fix.
        ceiling = await self._measured_overlay_ceiling(meta)
        if ceiling is not None and meta.mtu > ceiling:
            log.warning(
                "adopting session {} whose overlay MTU {} exceeds this node's underlay ceiling {} "
                "on {}; full-size frames will be dropped silently -- set the manager's network "
                "plugin `mtu` lower",
                meta.session_id,
                meta.mtu,
                ceiling,
                self._uplink,
            )
        # Devices are already up and carrying traffic; only the bookkeeping add_peer/add_endpoint
        # read is missing. The LOCAL subnet index is re-claimed from the journal by attach_endpoint,
        # which is idempotent per session. XFRM SAs survive in the kernel across an agent restart;
        # re-adopting the self VTEP lets add_peer reprogram them idempotently (`ip xfrm ... update`).
        if meta.encryption_key is not None and self_member.vtep_ip is None:
            # setup refuses this outright; adopt cannot, because the containers are already
            # running. Say it plainly instead: without a VTEP there is no `src` to anchor the SAs
            # on, so add_peer will refuse to open the tunnels and the session's cross-node traffic
            # stops here rather than continuing in clear text.
            log.warning(
                "adopting encrypted session {} on a node with no usable VTEP address: its peers "
                "cannot be reached until one is configured",
                meta.session_id,
            )
        if meta.encryption_key is None:
            try:
                await self._runner(link_up_args(vxlan_dev(meta.vni)))
            except (RuntimeError, OSError):
                log.warning("could not bring {} up while adopting", vxlan_dev(meta.vni))

    @override
    async def restore_session_peer_ownership(
        self, session_id: str, peers: Sequence[Member]
    ) -> None:
        """Rebuild XFRM ownership from the privileged executor's durable journal.

        Recovery invokes this for every live session before reclaiming dead ones. Marking the
        journalled pair as process-owned makes teardown complete, while `_pair_users` prevents one
        dead session from deleting a pair a live session still uses. Live sessions immediately
        force-reassert these pairs before their held-down tunnel is reopened.
        """
        meta = self._sessions.get(session_id)
        self_vtep = self._self_vteps.get(session_id)
        if meta is None or meta.encryption_key is None or self_vtep is None:
            return
        for peer_vtep in sorted({peer.vtep_ip for peer in peers if peer.vtep_ip is not None}):
            key = (self_vtep, peer_vtep, meta.vxlan_port)
            self._encrypted_peers.setdefault(session_id, set()).add(peer_vtep)
            self._pair_users.setdefault(key, set()).add(session_id)
            async with self._pair_journal.claiming(
                pair_key(*key), self._journal_owner, session_id
            ) as recorded:
                if not recorded:
                    # Adopting a pair whose claim will not record is the same hazard as
                    # programming one: another agent reads it as free and removes it. Leave the
                    # kernel state alone and let the drift re-assert retry.
                    log.error(
                        "not adopting ownership of the ESP pair {}->{}:{} for session {}: its"
                        " claim could not be recorded in the node-wide journal",
                        self_vtep,
                        peer_vtep,
                        meta.vxlan_port,
                        session_id,
                    )
                    self._pair_users.get(key, set()).discard(session_id)
                    continue
            self._programmed_pairs.add(key)

    @override
    async def prepare_recovery(self) -> None:
        """Hold every surviving Backend.AI VXLAN down before journal recovery.

        At this point no session metadata is trusted or even readable yet. Device ownership is the
        only durable fact available, so the backend prefix is intentionally the boundary: a valid
        journal later re-adopts and reopens plaintext sessions immediately and encrypted sessions
        only after their complete protection state is restored.
        """
        try:
            devices = await self._vxlan_lister()
        except Exception as e:
            raise OverlayEncryptionUnavailable(
                f"could not enumerate surviving {VXLAN_DEV_PREFIX} tunnels before recovery: {e}"
            ) from e
        failed: list[str] = []
        for device in sorted(name for name in devices if name.startswith(VXLAN_DEV_PREFIX)):
            if await self._hold_vxlan_down_or_absent(device):
                self._unclosed_devices.discard(device)
            else:
                failed.append(device)
        self._unclosed_devices.update(failed)
        if failed:
            # Do NOT prune. A claim is what stops another agent removing the SAs of a pair still
            # in use, and a tunnel that would not go down is exactly a pair that may still be
            # carrying traffic: dropping its claim while it is UP invites a co-located agent to
            # conclude it is the last user and delete the protection out from under it. Stale
            # claims cost a leaked SA; dropping a live one costs the guarantee.
            raise OverlayEncryptionUnavailable(
                "could not fail-close surviving VXLAN tunnel(s) before recovery: "
                + ", ".join(failed)
            )
        # Everything this node owned is down, so every claim of ours is stale by definition --
        # they outlive the process that made them, and a crash between programming a pair and
        # tearing it down leaves one with nobody behind it.
        pruned = await self._pair_journal.prune(self._journal_owner, live_sessions=())
        if pruned:
            log.info("dropped {} stale ESP pair claim(s) left by a previous life", pruned)

    async def _require_no_conflict(self, vni: int, dstport: int) -> None:
        """Refuse a VNI another VXLAN on this host already carries on the same port.

        The startup readiness check can only guess at the port: the manager configures it and
        allocates the VNI, and neither reaches this node until a session does. Here both are
        known, and an overlap is not advisory -- the plaintext-drop and mark rules select on
        (port, VNI) alone, so the two tunnels would act on each other's traffic in both
        directions with nothing reporting it.
        """
        conflict = await conflicting_device(port=dstport, vni=vni)
        if conflict is None:
            return
        raise OverlayEncryptionUnavailable(
            f"refusing VNI {vni} on udp/{dstport}: {conflict} on this host already carries that"
            " VNI on that port, so this session's firewall rules would match its frames and its"
            " traffic would be marked for this session's XFRM policy. Move one of the two off the"
            " shared port (the manager's `vxlan-port`) or out of the VNI range."
        )

    async def prune_pair_claims(self, live_sessions: Collection[str]) -> int:
        """Drop this node's ESP pair claims for sessions it no longer has.

        Deferred until every surviving tunnel is actually down: a claim is what stops another
        agent removing the SAs of a pair still in use, so pruning one whose device is still UP is
        the same hazard the recovery preflight exists to avoid.
        """
        return await self._pair_journal.prune(self._journal_owner, live_sessions)

    def unclosed_devices(self) -> frozenset[str]:
        """Surviving tunnels this node has not managed to bring down, for diagnostics."""
        return frozenset(self._unclosed_devices)

    async def retry_fail_close(self) -> frozenset[str]:
        """Try again to bring down every survivor recovery could not close. Returns what is left.

        Called on a timer as well as before setup: `prepare_recovery` raising does not stop the
        privnet -- it continues in degraded mode on purpose -- so without a retry an orphan whose
        session is not in the journal stays UP for as long as the process runs, carrying whatever
        a previous life was carrying, with nothing coming back to it.
        """
        for dev in sorted(self._unclosed_devices):
            if await self._hold_vxlan_down_or_absent(dev):
                self._unclosed_devices.discard(dev)
                log.info("surviving tunnel {} is finally down", dev)
        return frozenset(self._unclosed_devices)

    async def _require_closed(self, vni: int) -> None:
        """Refuse to build any overlay while a survivor from a previous life is still up.

        Not just the VNI that names it. This node cannot say what an unclosed tunnel is carrying,
        and it shares the underlay port, the XFRM pairs and the firewall chains with whatever is
        set up next -- so admitting a different VNI is admitting a session onto state nobody owns.
        Refusing everything is the loud failure; the alternative is a session that comes up beside
        it and quietly inherits its traffic.
        """
        remaining = await self.retry_fail_close()
        if not remaining:
            return
        raise OverlayEncryptionUnavailable(
            f"refusing to set up VNI {vni}: {', '.join(sorted(remaining))} survived a previous"
            " life on this node and could not be brought down, so what they are carrying is"
            " unknown. Remove them by hand (`ip link del`) once their traffic is accounted for."
        )

    @override
    @override
    async def withdraw_session_network(self, session_id: str) -> None:
        """Give up this node's OWNERSHIP of a session without touching the shared data plane.

        For the agent whose kernels of a session leave while another agent on the same host still
        has some: the devices and the LOCAL block are the node's, so they stay -- but this
        process's claim on the ESP pairs, and its watchdog's belief that it is responsible for
        this session, must not. Left behind, the watchdog goes on reprogramming a session it no
        longer serves, and the claim keeps the pair alive after the last agent has gone.
        """
        async with self._session_guard(session_id):
            meta = self._sessions.get(session_id)
            self_vtep = self._self_vteps.get(session_id)
            if meta is not None and self_vtep is not None:
                unreleased: list[str] = []
                for peer_vtep in sorted(self._encrypted_peers.get(session_id, set())):
                    key = (self_vtep, peer_vtep, meta.vxlan_port)
                    # The claim, not the SAs: another agent here is still carried by them, which
                    # is exactly what the node-wide refcount is for.
                    async with self._pair_journal.releasing(
                        pair_key(*key), self._journal_owner, session_id
                    ) as freed:
                        if freed is None:
                            # The journal could not say. Our claim may still be on disk, and
                            # reporting the withdrawal as done leaves it there with nobody
                            # left to remove it.
                            unreleased.append(peer_vtep)
                    self._pair_users.get(key, set()).discard(session_id)
                if unreleased:
                    raise OverlayEncryptionUnavailable(
                        f"session {session_id} could not release its ESP pair claim for"
                        f" {', '.join(unreleased)}; this node has not let the session go"
                    )
            await self._forget_session(session_id)
        self._session_guards.pop(session_id, None)

    @override
    async def teardown_session_network(self, session_id: str) -> None:
        """Remove everything this node holds for the session, or keep owning what is left.

        Ordered so the dangerous states cannot be reached: the device goes down before any XFRM
        object is removed (else queued traffic leaves in clear text), and this node's record of
        the session is dropped only once every removal has actually succeeded. "Already gone"
        counts as success; anything else keeps the record so the caller can retry against the
        same session instead of losing track of live host state -- see `OverlayTeardownIncomplete`.
        """
        async with self._session_guard(session_id):
            await self._teardown_guarded(session_id)
        self._session_guards.pop(session_id, None)

    async def _teardown_guarded(self, session_id: str) -> None:
        """The body of `teardown_session_network`, with the session's guard held.

        Held for the whole of it so the protection watchdog cannot be midway through reinstalling
        what this is removing.
        """
        meta = self._sessions.get(session_id)
        # Confirm the device is closed before removing any XFRM object. Even teardown may race
        # queued traffic or a surviving FDB entry; deleting the policy first would let that packet
        # leave in clear text. If link-down fails, retain all bookkeeping so teardown can retry.
        if meta is not None and meta.vni is not None and meta.encryption_key is not None:
            dev = vxlan_dev(meta.vni)
            if not await self._hold_vxlan_down_or_absent(dev):
                raise OverlayEncryptionUnavailable(
                    f"encrypted session {session_id}'s VXLAN {dev} could not be brought down; "
                    "retaining teardown ownership for retry"
                )
        # Read, do not release: the index names the LOCAL bridge deleted below, and a release
        # before the delete makes the device unfindable on a retry. Read, not allocate -- teardown
        # of a session this node never set up must not mint an index and then delete the bridge
        # that index names.
        local_index = await self._local_subnets.lookup(session_id)
        failures: list[str] = []
        if meta is not None and meta.vni is not None:
            await self._remove_session_state(meta, session_id, meta.vni, local_index, failures)
        if failures:
            raise OverlayTeardownIncomplete(
                f"session {session_id} left overlay state on this node "
                f"({len(failures)}): " + "; ".join(failures)
            )
        await self._forget_session(session_id)
        await self._local_subnets.release(session_id)

    async def _remove_session_state(
        self,
        meta: SessionNetMeta,
        session_id: str,
        vni: int,
        local_index: int | None,
        failures: list[str],
    ) -> None:
        """Every host object this session owns, in dependency order, collecting what would not go."""
        # XFRM lives in the netns, not on the device: deleting the vxlan link below leaves any SA
        # and policy behind. `del_peer` cannot be relied on to have run for every peer first -- a
        # peer node can vanish, or teardown can win the race -- and a leftover outbound policy is
        # actively harmful rather than untidy: it selects ESP for this node pair's VXLAN UDP even
        # after the SA is gone, so later plaintext traffic on the same port is dropped wholesale.
        # Measured before pair refcounting: one node kept `SAD 2 / SPD 1` pointing at a dead peer.
        # Both objects must therefore be released together after their last user leaves.
        self_vtep = self._self_vteps.get(session_id)
        for peer_vtep in sorted(self._encrypted_peers.get(session_id, set())):
            await self._unprogram_encryption(meta, session_id, peer_vtep, self_vtep, failures)
        await self._del_forward_accept(vni, failures)
        if meta.encryption_key is not None:
            await self._del_output_mark(vni, meta.vxlan_port, failures)
            await self._del_egress_guard(vni, meta.vxlan_port, failures)
            await self._del_plaintext_drop(vni, meta.vxlan_port, failures)
        devs = [bridge_dev(vni), vxlan_dev(vni)]
        if local_index is not None:
            devs.append(local_bridge_dev(local_index))
        # `bailo<vni>` is the transitional name (see setup) and is removed alongside -- but only
        # where it cannot be some other session's live LOCAL bridge. The two names share a number
        # space: LOCAL indices run 0..layout.size-1 and VNIs start at 4096, so the default layout
        # (a /16 pool in /26 blocks -> 1024 indices) can never collide. A layout that asks for more
        # sessions per node than that can: /16 in /30 blocks gives 16384 indices, and index 4097 is
        # spelled exactly like VNI 4097's transitional device. Deleting it would cut a running
        # session's containers off their gateway. Not a misconfiguration to refuse -- wanting more
        # sessions on a node is reasonable -- so bound the cleanup instead.
        if vni >= self._local_subnets.layout.size:
            devs.append(local_bridge_dev(vni))
        for dev in devs:
            await self._remove(link_del_args(dev), failures)

    async def _forget_session(self, session_id: str) -> None:
        """Drop this node's record of the session. Called only after every removal succeeded."""
        self._sessions.pop(session_id, None)
        self._self_vteps.pop(session_id, None)
        self._encrypted_peers.pop(session_id, None)
        self._reach_probed.pop(session_id, None)
        self._unreachable_peers.pop(session_id, None)
        self._remote_endpoints.pop(session_id, None)
        for key in [key for key in self._forwarding_locks if key[0] == session_id]:
            self._forwarding_locks.pop(key, None)
        self._security_states.pop(session_id, None)
        for task in self._reach_tasks.pop(session_id, set()):
            task.cancel()

    @override
    async def ensure_session_security(self, session_id: str, peers: Sequence[Member]) -> None:
        """Re-assert this session's plaintext drop and its ESP pairs, and raise if it cannot.

        The reconcile that calls this only visits peers whose published record changed, and none of
        the ways this state disappears change a record: an `iptables -F`, a firewall reload, an
        `ip xfrm state flush`. Without a pass that looks at the state itself rather than at the
        diff, the first of those silently reopens the session to injected plaintext and the last
        silently sends its traffic in clear, for as long as the session runs.

        Firewall rules are checked before insertion. Same-generation SAs may replay `add` as
        `update`; generation changes delete and recreate only the expired SPI slot so AEAD key
        material is actually replaced.
        """
        meta = self._sessions.get(session_id)
        if meta is None or meta.encryption_key is None:
            return
        machine = self._security_states.get(session_id)
        if machine is not None and machine.state is VxlanSecurityState.BLOCKING:
            # A prior link-down failed. Protection must not be rebuilt on top of an unconfirmed
            # open path and then mistaken for a normal restore: retry the physical block first.
            await self._close_tunnel(
                meta,
                session_id,
                machine.failure_reason or "the overlay tunnel has not been confirmed down",
            )
            if machine.state is VxlanSecurityState.BLOCKING:
                raise OverlayEncryptionUnavailable(
                    f"session {session_id}'s overlay tunnel could not be brought down; security "
                    "reconciliation is deferred until the fail-closed state is confirmed"
                )
        self._transition_security(session_id, VxlanSecurityEvent.RECONCILE_STARTED)
        if not await self._firewall_side_ok(meta, session_id):
            # The tunnel is already held down by the call above; raising is what keeps the peers
            # out of the coordinator's applied set so they are reprogrammed once it comes back.
            raise OverlayEncryptionUnavailable(
                f"session {session_id} is encrypted but its plaintext-drop rule could not be "
                "restored; the overlay tunnel is held down until it can"
            )
        # The published membership, not `_encrypted_peers`: a process that restarted under a
        # running session has an empty one, and nothing refills it -- the agent's reconcile does
        # not resend a peer whose record has not changed. Measured: after a privnet restart no
        # add_peer ever arrived, so teardown left this node's SAs *and policies* behind, and a
        # leftover policy selects ESP for that node pair with no SA to satisfy it.
        for peer_vtep in sorted(
            {peer.vtep_ip for peer in peers if peer.vtep_ip is not None}
            | self._encrypted_peers.get(session_id, set())
        ):
            try:
                if not await self._program_encryption(meta, session_id, peer_vtep, force=True):
                    raise OverlayEncryptionUnavailable(
                        f"session {session_id} cannot re-assert the ESP pair for {peer_vtep}: "
                        "this node's VTEP is unavailable"
                    )
            except Exception:
                # The FDB entry for this peer is already open -- this is a re-assert, not a first
                # program -- so a failure here is not "the peer is unreachable" but "the peer is
                # reachable and may be unprotected". Forget the pair (so nothing downstream trusts
                # a stale success) and close the tunnel, which is the only thing that stops the
                # session sending in clear while the SAs are missing.
                self._forget_pair(meta, session_id, peer_vtep)
                await self._close_tunnel(
                    meta,
                    session_id,
                    f"the ESP pair for {peer_vtep} could not be re-asserted",
                )
                raise
        if not await self._reopen_tunnel(meta, session_id):
            raise OverlayEncryptionUnavailable(
                f"session {session_id}'s security state was restored but its overlay tunnel "
                "could not be reopened"
            )

    @override
    async def add_peer(self, session_id: str, peer: Member) -> None:
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None or peer.vtep_ip is None:
            return
        # Encryption first, FDB second. The FDB entry is what makes a frame leave this node for
        # that peer, so opening it before the ESP policy exists is a window in which an "encrypted"
        # session sends clear text. Doing it in this order makes the failure mode "the peer is
        # unreachable" instead of "the peer is reachable and unprotected", and unreachable is the
        # one a caller can see.
        # Raise rather than return: the caller records a peer that came back without an error as
        # applied, and then skips it for as long as its record does not change -- so a silent
        # refusal here would be remembered as success and never retried, which is the shape of
        # "the firewall came back and the session stayed unprotected".
        async with self._forwarding_lock(session_id, peer.vtep_ip):
            if not await self._firewall_side_ok(meta, session_id):
                raise OverlayEncryptionUnavailable(
                    f"not opening the tunnel to {peer.vtep_ip} for session {session_id}: the "
                    "session's receive side is not closed"
                )
            if not await self._program_encryption(meta, session_id, peer.vtep_ip):
                # The session asked for encryption and this node cannot provide it for this peer.
                # Appending the FDB entry anyway is the fail-open case the ordering above exists to
                # avoid -- it would open exactly the path the session was promised would be protected.
                raise OverlayEncryptionUnavailable(
                    f"not opening the tunnel to {peer.vtep_ip} for session {session_id}: this node "
                    "could not program the SAs for that peer"
                )
            await self._runner(fdb_append_args(meta.vni, peer.vtep_ip))

    async def _program_encryption(
        self, meta: SessionNetMeta, session_id: str, peer_vtep: str, *, force: bool = False
    ) -> bool:
        """Program the ESP pair for this peer. False means the session wanted encryption and this
        pair did not get it -- the caller must not open the path."""
        if meta.encryption_key is None or meta.vni is None:
            return True  # nothing to protect: an unencrypted session opens normally
        self_vtep = self._self_vteps.get(session_id)
        if self_vtep is None:
            # setup refuses an encrypted session on a node with no VTEP, so this is the adopt
            # path: an agent restarting under a running session whose node lost its VTEP.
            log.warning(
                "cannot encrypt overlay for session {}: this node's VTEP is unknown", session_id
            )
            return False
        # Recorded BEFORE the commands run, not after. A failure partway can leave an SA or a
        # policy installed, and an unrecorded one is never unprogrammed -- a stranded policy selects
        # ESP for this node pair with no SA to satisfy it, and the next session between the two is
        # dropped wholesale. Over-recording costs one best-effort delete; under-recording costs a
        # dead overlay.
        #
        # But the record must not double as "this pair is programmed": a failure would then make
        # every retry take the `already programmed` shortcut below and the pair would stay
        # half-built for good. So the two are separate -- `_pair_users` says who would have to
        # release it, `_programmed_pairs` says whether the kernel actually has it.
        key = (self_vtep, peer_vtep, meta.vxlan_port)
        # Under the pair's lock, so the refcount below and the commands that follow from it cannot
        # interleave with another session's teardown of the same pair -- see `_pair_locks`.
        async with self._pair_lock(key):
            self._encrypted_peers.setdefault(session_id, set()).add(peer_vtep)
            self._pair_users.setdefault(key, set()).add(session_id)
            # The host lock is held from here through the SA/policy programming below. Recording
            # the claim and installing what it claims are one step: between them, another agent
            # can read the pair as unused and delete the very objects being installed.
            async with self._pair_journal.claiming(
                pair_key(*key), self._journal_owner, session_id
            ) as recorded:
                if not recorded:
                    # Refuse rather than program. The claim is what another agent process counts
                    # when it decides whether the pair is still in use; with ours not on disk, it
                    # reads the pair as free and deletes the very SAs about to be installed --
                    # and a marker kept in this process cannot tell it otherwise. So the honest
                    # answer is that this node cannot protect the peer, which is what the caller
                    # already knows how to handle: no FDB entry, no clear-text path.
                    log.error(
                        "not programming the ESP pair {}->{}:{} for session {}: its claim could"
                        " not be recorded in the node-wide journal, so a co-located agent could"
                        " delete the SAs while this session is using them",
                        self_vtep,
                        peer_vtep,
                        meta.vxlan_port,
                        session_id,
                    )
                    self._pair_users.get(key, set()).discard(session_id)
                    self._encrypted_peers.get(session_id, set()).discard(peer_vtep)
                    return False
                return await self._program_pair_locked(
                    meta, session_id, peer_vtep, self_vtep, key, force=force
                )

    async def _program_pair_locked(
        self,
        meta: SessionNetMeta,
        session_id: str,
        peer_vtep: str,
        self_vtep: str,
        key: tuple[str, str, int],
        *,
        force: bool,
    ) -> bool:
        """Program this pair's SAs and policy, with its host-wide claim lock held.

        Split out only so the lock can span the whole programming: the claim it records is what
        stops another agent reading the pair as unused and deleting these very objects.
        """
        if meta.encryption_key is None:
            return True
        if True:
            observed_generation = self._key_generation()
            generation = max(
                observed_generation,
                self._pair_active_generations.get(key, observed_generation),
            )
            target_generations = (generation - 1, generation, generation + 1)
            target_slots = {
                target_generation % _KEYRING_SIZE: target_generation
                for target_generation in target_generations
            }
            slot_generations = self._pair_slot_generations.setdefault(key, {})
            if key in self._programmed_pairs and slot_generations == target_slots and not force:
                return True  # another session on this node already programmed this pair
            try:
                for target_generation in target_generations:
                    slot = target_generation % _KEYRING_SIZE
                    add_args = xfrm_state_add_args(
                        self_vtep,
                        peer_vtep,
                        meta.encryption_key,
                        generation=target_generation,
                    )
                    if slot_generations.get(slot) == target_generation:
                        if force:
                            for args in add_args:
                                await self._run_xfrm(args)
                        continue

                    # A Linux XFRM state update does not replace AEAD key material reliably. The
                    # stale generation in this slot is outside the accepted three-generation
                    # window, so delete it and create the slot with the new key instead. A missing
                    # delete is harmless; a failed delete followed by EEXIST on add is surfaced,
                    # never downgraded to an in-place update with the old key.
                    for args in xfrm_state_del_args(
                        self_vtep, peer_vtep, generation=target_generation
                    ):
                        try:
                            await self._runner(args)
                        except RuntimeError:
                            pass
                    for args in add_args:
                        await self._runner(args)
                    slot_generations[slot] = target_generation

                # Switch outbound traffic only after every receiving generation is installed. The
                # exact SPI makes the policy select the current generation, while adjacent nodes
                # whose clocks straddle the boundary can still receive previous/next traffic.
                for args in xfrm_policy_add_args(
                    self_vtep,
                    peer_vtep,
                    dstport=meta.vxlan_port,
                    generation=generation,
                ):
                    await self._runner(args)
                self._pair_active_generations[key] = generation
            except Exception:
                self._programmed_pairs.discard(key)
                # The SA/policy belongs to every session between this node pair. A partial rekey
                # can affect all of them, so holding down only the session that happened to run
                # this reconcile would leave its siblings open on uncertain shared state.
                for user_session_id in sorted(self._pair_users.get(key, set())):
                    if (user_meta := self._sessions.get(user_session_id)) is not None:
                        await self._close_tunnel(
                            user_meta,
                            user_session_id,
                            f"the shared ESP pair for {peer_vtep} failed to rekey",
                        )
                raise
            # Only now. Anything that raised above left the pair unmarked, so the next reconcile
            # retries it -- and the FDB entry that would have carried clear text was never
            # appended, because add_peer programs before it opens the path.
            self._programmed_pairs.add(key)
        return True

    async def _unprogram_encryption(
        self,
        meta: SessionNetMeta,
        session_id: str,
        peer_vtep: str,
        self_vtep: str | None,
        failures: list[str] | None = None,
    ) -> None:
        """Remove this session's ESP SA pair, and the shared policy once nobody is left on it.

        Idempotent, and reports what it could not remove rather than assuming success (a
        surviving SA or policy is not untidiness -- see `OverlayTeardownIncomplete`). The SAs are
        this session's (the SPI folds the VNI in) and go
        unconditionally; the policy belongs to every session between the same two nodes on the same
        port, so it goes only when the last of them does. Deleting it with the first session to end
        is what silently drops the others to clear text -- they keep running, their SAs are still
        there, and nothing selects them any more.
        """
        if meta.encryption_key is None or meta.vni is None or self_vtep is None:
            self._encrypted_peers.get(session_id, set()).discard(peer_vtep)
            return
        key = (self_vtep, peer_vtep, meta.vxlan_port)
        # Under the pair's lock, from the refcount decision through the deletes it authorises. The
        # two are one step: without the lock, another session can program this very pair between
        # "nobody is left" and the delete, and be left holding an open FDB with nothing to encrypt
        # it -- see `_pair_locks`.
        async with self._pair_lock(key):
            await self._unprogram_pair(meta, session_id, peer_vtep, self_vtep, key, failures)

    async def _unprogram_pair(
        self,
        meta: SessionNetMeta,
        session_id: str,
        peer_vtep: str,
        self_vtep: str,
        key: tuple[str, str, int],
        failures: list[str] | None = None,
    ) -> None:
        """The body of `_unprogram_encryption`, run with the pair's lock held."""
        async with self._pair_journal.releasing(
            pair_key(*key), self._journal_owner, session_id
        ) as node_wide_free:
            await self._unprogram_pair_locked(
                meta, session_id, peer_vtep, self_vtep, key, node_wide_free, failures
            )

    async def _unprogram_pair_locked(
        self,
        meta: SessionNetMeta,
        session_id: str,
        peer_vtep: str,
        self_vtep: str,
        key: tuple[str, str, int],
        node_wide_free: bool | None,
        failures: list[str] | None,
    ) -> None:
        """The body of `_unprogram_pair`, with the pair's host-wide lock held.

        ``node_wide_free`` is the journal's answer: True to remove, False to leave, None when it
        could not be determined. Unknown is NOT permission. Of the two ways to be wrong, a stale
        SA keeps traffic encrypted while a deleted one takes down whoever else was on it -- and
        the same reasoning applies to a pair whose claim never reached the journal at all.
        """
        users = self._pair_users.get(key, set())
        # Only an explicit True frees the pair. Unknown is not permission: the journal is what
        # every process on this node agrees on, and an answer it could not give is not one.
        if (users - {session_id}) or node_wide_free is not True:
            # Another session -- possibly another agent's on this same host -- is still carried
            # by this pair's SA and policy. Nothing to delete, so the refcount settles here.
            users.discard(session_id)
            self._encrypted_peers.get(session_id, set()).discard(peer_vtep)
            return
        if key not in self._programmed_pairs:
            # This process did not program the pair, so it does not know who else is on it. That
            # happens when only the privnet restarted: the agent's coordinator still remembers its
            # peers as applied and never re-sends them, so the refcount here rebuilds as empty
            # while other sessions are still carried by the very SA and policy about to be removed.
            #
            # Deleting on that empty count is what drops those sessions to clear text -- their SAs
            # remain, nothing selects them any more, and nothing says so. Leaking the pair instead
            # costs one stale SA and policy per node pair until the kernel or an operator clears
            # them; of the two ways to be wrong, that is the one that keeps traffic encrypted.
            log.warning(
                "not removing the ESP pair {}->{}:{} for session {}: this process did not program"
                " it (privnet restart?), so it cannot tell whether another session still needs it",
                self_vtep,
                peer_vtep,
                meta.vxlan_port,
                session_id,
            )
            users.discard(session_id)
            self._pair_users.pop(key, None)
            self._encrypted_peers.get(session_id, set()).discard(peer_vtep)
            return
        # SA first, then the policy. Between the two there is a window, and this order makes it a
        # window where traffic is blocked (a policy with no SA) rather than one where it leaves in
        # clear text (a live tunnel with nothing requiring ESP). Nothing should be flowing here --
        # this runs when the last session on the pair is gone -- but of the two ways to be wrong,
        # dropping is the one to pick.
        state_deletes = [
            args
            for slot in range(_KEYRING_SIZE)
            for args in xfrm_state_del_args(self_vtep, peer_vtep, generation=slot)
        ]
        # Delete first, THEN forget. The other order looks harmless because teardown reports the
        # failure -- but the retry it is asking for reads `_encrypted_peers` to find the pairs to
        # revisit, and that entry is already gone. The retry then finds nothing to do, succeeds,
        # and the manager releases the VNI over an SA and policy that are still on the host.
        # Collect into the caller's list when it is collecting, and let `_remove` raise when it
        # is not. Keeping the two in one variable is what forced the cast away: with no list,
        # nothing reaches the branch below because the raise has already left.
        pair_failures: list[str] | None = [] if failures is not None else None
        for args in (
            *state_deletes,
            *xfrm_policy_del_args(self_vtep, peer_vtep, dstport=meta.vxlan_port),
        ):
            await self._remove(args, pair_failures)
        if failures is not None and pair_failures:
            failures.extend(pair_failures)
            return  # bookkeeping untouched, so the next teardown visits this pair again
        self._programmed_pairs.discard(key)
        self._pair_slot_generations.pop(key, None)
        self._pair_active_generations.pop(key, None)
        users.discard(session_id)
        self._pair_users.pop(key, None)
        self._encrypted_peers.get(session_id, set()).discard(peer_vtep)

    async def _run_xfrm(self, argv: Sequence[str]) -> None:
        """Run one `ip xfrm` command, replaying a state `add` as `update` when it already exists.

        Kernel SAs outlive the agent process, so a restart re-programs onto an existing one; `add`
        is EEXIST there and `update` is the in-place replace. Only that one case is retried -- any
        other failure is the caller's to see.
        """
        try:
            await self._runner(argv)
        except RuntimeError:
            if list(argv[:4]) != ["ip", "xfrm", "state", "add"]:
                raise
            await self._runner(["ip", "xfrm", "state", "update", *argv[4:]])

    @override
    async def del_peer(self, session_id: str, peer: Member) -> None:
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None or peer.vtep_ip is None:
            return
        async with self._forwarding_lock(session_id, peer.vtep_ip):
            remaining = sorted(
                f"{ip}/{mac}"
                for (ip, mac), vtep_ip in self._remote_endpoints.get(session_id, {}).items()
                if vtep_ip == peer.vtep_ip
            )
            if remaining:
                raise OverlayEncryptionUnavailable(
                    f"not withdrawing encryption for VTEP {peer.vtep_ip} in session {session_id}: "
                    f"endpoint FDB entries still exist ({', '.join(remaining)})"
                )
            # Close forwarding first. Withdrawing XFRM while even the broadcast FDB remains opens
            # a clear-text window; a failed FDB delete is therefore retried, not swallowed.
            # Idempotent on absence only: an entry an external cleanup or a restart already
            # removed must not make the coordinator retry this withdrawal forever, while a
            # permission error or a held lock still has to stop it (a live FDB entry with the
            # XFRM pair withdrawn underneath it is a clear-text path).
            await self._remove(fdb_del_args(meta.vni, peer.vtep_ip))
            await self._unprogram_encryption(
                meta, session_id, peer.vtep_ip, self._self_vteps.get(session_id)
            )

    @override
    async def add_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        """Proactively program a remote endpoint: unicast MAC→VTEP FDB + permanent ARP.

        Idempotent (``replace``). Known unicast then never floods over the tunnel."""
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None:
            return
        # The same fail-closed rule add_peer follows. This path is reached from the membership
        # reconcile, which runs whether or not add_peer succeeded, and a unicast FDB entry opens a
        # route to that VTEP on its own -- the broadcast entry add_peer withheld is not what a
        # frame with a known destination MAC needs. Without this check a peer whose SAs failed to
        # program is still reachable, in clear text, as soon as its endpoint is published.
        # Raising, for the same reason as add_peer: an endpoint that returns without an error is
        # recorded as applied and not visited again.
        async with self._forwarding_lock(session_id, vtep_ip):
            if not await self._firewall_side_ok(meta, session_id):
                raise OverlayEncryptionUnavailable(
                    f"not programming the endpoint {ip} for session {session_id}: the session's "
                    "receive side is not closed"
                )
            if not self._pair_is_protected(meta, session_id, vtep_ip):
                raise OverlayEncryptionUnavailable(
                    f"not programming the endpoint {ip} ({mac}) for session {session_id}: the "
                    f"session is encrypted and the SAs for VTEP {vtep_ip} are not in place"
                )
            await self._runner(fdb_replace_args(meta.vni, mac, vtep_ip))
            # Record immediately after the forwarding path opens. A neighbour failure must not
            # make DEL_PEER believe the already-installed FDB does not exist.
            self._remote_endpoints.setdefault(session_id, {})[(ip, mac)] = vtep_ip
            await self._runner(neigh_replace_args(meta.vni, ip, mac))
        self._start_reach_probe(session_id, meta, ip=ip, mac=mac, vtep_ip=vtep_ip)

    def _start_reach_probe(
        self, session_id: str, meta: SessionNetMeta, *, ip: str, mac: str, vtep_ip: str
    ) -> None:
        """Check in the background that the tunnel to a REMOTE endpoint carries traffic.

        Only remote ones: a local endpoint is reached over the bridge without touching the tunnel,
        so probing it would prove nothing about the thing that silently breaks.

        Background and non-fatal by design. This runs on the membership-reconcile path, which must
        not stall, and the endpoint's container may still be starting -- refusing a session on a
        probe that was merely early would be worse than the silence it replaces. A loud, greppable
        error naming the remedy is the whole gain.
        """
        if meta.vni is None or self._self_vteps.get(session_id) == vtep_ip:
            return
        probed = self._reach_probed.setdefault(session_id, set())
        if vtep_ip in probed:
            # Already asked about this peer for this session. Every kernel behind it rides the same
            # tunnel, so asking once per kernel would multiply tasks and raw sockets by the peer's
            # kernel count for an answer that cannot differ.
            return
        probed.add(vtep_ip)
        # Bound here, not inside the closure: the guard above narrows `meta.vni` only in this
        # scope, and a nested function would read it as `int | None` again.
        bridge = bridge_dev(meta.vni)

        async def _run() -> None:
            for attempt in range(1, _REACH_ATTEMPTS + 1):
                answered = await self._reach_probe(bridge, ip, mac)
                if answered is None:
                    log.debug("overlay reach probe unavailable on {}; skipping", bridge)
                    return  # left marked: an unavailable probe will be unavailable next time too
                if answered:
                    log.debug(
                        "overlay reach probe: {} answered over {} (attempt {})",
                        ip,
                        bridge,
                        attempt,
                    )
                    self._unreachable_peers.get(session_id, set()).discard(vtep_ip)
                    return
                if attempt < _REACH_ATTEMPTS:
                    await asyncio.sleep(_REACH_RETRY_DELAY_SEC)
            log.error(
                "session {}: the overlay to {} ({} via VTEP {}) carries no traffic -- {} ARP "
                "probes over {} went unanswered. The devices are up and the FDB is programmed, so "
                "suspect the pod network filtering the tunnel: Calico drops workload UDP on its "
                "felix vxlanPort (4789 by default, which this session uses: {}) in every "
                "encapsulation mode. Move the session's port with the manager's network plugin "
                "`vxlan-port`, or check for a firewall on that UDP port between the nodes.",
                session_id,
                ip,
                mac,
                vtep_ip,
                _REACH_ATTEMPTS,
                bridge,
                meta.vxlan_port,
            )
            self._unreachable_peers.setdefault(session_id, set()).add(vtep_ip)
            # Unmarked, so the next endpoint behind this peer probes again. The first one may have
            # been early -- its container was still starting -- and a peer written off on that is a
            # peer nothing ever asks about again.
            self._reach_probed.get(session_id, set()).discard(vtep_ip)

        task = asyncio.create_task(_run())
        tasks = self._reach_tasks.setdefault(session_id, set())
        tasks.add(task)
        task.add_done_callback(tasks.discard)

    @override
    async def del_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None:
            return
        async with self._forwarding_lock(session_id, vtep_ip):
            # The FDB is the forwarding capability. Its removal must land before the peer's XFRM
            # can be withdrawn, so failures propagate to the coordinator and keep the endpoint
            # applied for retry. Neighbour cleanup cannot transmit by itself and remains best-effort.
            # Absent is done -- an entry an external cleanup already removed must not park the
            # coordinator on this withdrawal -- while EPERM or a held lock still propagates.
            await self._remove(fdb_del_args(meta.vni, vtep_ip, mac=mac))
            self._remote_endpoints.get(session_id, {}).pop((ip, mac), None)
            try:
                await self._remove(neigh_del_args(meta.vni, ip))
            except (RuntimeError, OSError):
                log.debug("could not remove the neighbour entry {} in {}", ip, session_id)

    @override
    async def setup_dns_redirect(self, session_id: str, loopback_port: int) -> None:
        # In-process (privileged agent) path: this backend holds CAP_NET_ADMIN, so install the
        # :53 -> 127.0.0.1:<port> redirect directly. In privnet mode the proxy sends this to the
        # privnet instead. Idempotent (replaces any prior rule).
        if (subnet := await self._local_subnets.subnet_of(session_id)) is not None:
            await redirect_session_dns(subnet, loopback_port, session_id)

    @override
    async def teardown_dns_redirect(self, session_id: str) -> None:
        await remove_dns_redirect(session_id)

    @override
    async def attach_endpoint(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
    ) -> EndpointPlan:
        # Static IP at the manager-assigned overlay address (disjoint across nodes); falls
        # back to host-local only if the manager did not assign one (single-node / legacy).
        overlay_ip = kernel_config.get("cluster_network_ip")
        return EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="eth0",
                    role=NetworkRole.LOCAL,
                    is_default_route=True,
                    cni_config=local_cni_config(
                        meta.session_id,
                        # Same index the subnet below is cut from, so the device and the address
                        # it carries cannot drift apart.
                        bridge=local_bridge_dev(await self._local_index(meta.session_id)),
                        subnet=await self._local_subnet(meta.session_id),
                    ),
                ),
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name=OVERLAY_IFNAME,
                    role=NetworkRole.OVERLAY,
                    cni_config=overlay_cni_config(meta, overlay_ip),
                    # overlay_cni_config raises when overlay_ip is None, so the guard is defensive.
                    cni_capability_args=(
                        overlay_mac_capability_args(overlay_ip) if overlay_ip else None
                    ),
                ),
            ]
        )

    @override
    async def detach_endpoint(self, kernel: AbstractKernel) -> None:
        pass
