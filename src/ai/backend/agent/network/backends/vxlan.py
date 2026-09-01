"""VXLAN cluster-network backend (BEP-1062).

Portable default data plane: per-session VXLAN VNI + bridge, with unicast head-end
replication (FDB) driven by the SessionNetworkCoordinator's etcd membership watch.

The side-effecting ``ip``/``bridge`` invocations are isolated behind an injectable
runner; the command builders and CNI-config assembly are pure and unit-tested.
"""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Final, override

from ai.backend.agent.errors.network import (
    OverlayAddressNotAssigned,
    OverlayEncryptionUnavailable,
    OverlayMtuTooLarge,
)
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.network.caps import probe_caps
from ai.backend.agent.network.local_subnet import LocalSubnetAllocator, get_local_subnet_allocator
from ai.backend.agent.network.native_attacher import redirect_session_dns, remove_dns_redirect
from ai.backend.agent.network.overlay_probe import arp_probe
from ai.backend.agent.network.path_mtu import underlay_mtu
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
MtuProbe = Callable[[str], Awaitable[int | None]]
# (bridge, target_ip, target_mac) -> answered? / None when the probe could not run.
ReachProbe = Callable[[str, str, str], Awaitable[bool | None]]

# A freshly published endpoint may belong to a container that is still starting, so the reach
# probe is retried before it is believed. Cheap (one ARP frame each) and bounded.
_REACH_ATTEMPTS: Final = 5
_REACH_RETRY_DELAY_SEC: Final = 3.0


# --- naming (kept within the 15-char interface name limit) ---


def vxlan_dev(vni: int) -> str:
    return f"baivx{vni}"


def bridge_dev(vni: int) -> str:
    return f"baibr{vni}"


# --- pure command builders ---


def vxlan_link_add_args(
    vni: int, uplink: str, *, mtu: int | None = None, dstport: int = VXLAN_DSTPORT
) -> list[str]:
    # ``mtu`` is the OVERLAY MTU (the inner frame the tunnel carries), which the manager already
    # computed as underlay - overhead. Setting it explicitly ties the vxlan device, the overlay
    # bridge and the container NIC to one value instead of relying on the kernel's auto-calc
    # (uplink - 50) happening to match — which silently diverges the moment this node's uplink MTU
    # differs from the manager's assumption, reopening the black hole.
    # ``mtu`` is a generic link property and MUST precede ``type vxlan``: after it, ``ip`` parses
    # the next token (our ``id``) as a vxlan sub-option and errors out. Verified against iproute2.
    mtu_args = ["mtu", str(mtu)] if mtu is not None else []
    return [
        "ip", "link", "add", vxlan_dev(vni), *mtu_args,
        "type", "vxlan",
        "id", str(vni),
        "dev", uplink,
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


def _esp_spi(vni: int, src: str, dst: str) -> int:
    """A deterministic 32-bit SPI for the directed VTEP pair, so both ends agree without a handshake:
    A's out-SA (src=A,dst=B) and B's in-SA (src=A,dst=B) compute the same value. The VNI is folded in
    so concurrent sessions on one node do not collide. Kept above 255 (SPIs 0-255 are reserved)."""
    digest = hashlib.sha256(f"{vni}:{src}:{dst}".encode()).digest()
    return (int.from_bytes(digest[:4], "big") % (2**32 - 256)) + 256


def _aead_key(key_hex: str) -> str:
    """rfc4106(gcm(aes)) keys carry a 4-byte salt after the cipher key. Derive the salt from the key
    (identical on both ends) and append it, so the 256-bit session key becomes a valid AEAD key."""
    salt = hashlib.sha256(bytes.fromhex(key_hex)).digest()[:4]
    return "0x" + key_hex + salt.hex()


def xfrm_state_add_args(self_vtep: str, peer_vtep: str, vni: int, key_hex: str) -> list[list[str]]:
    """The ESP SA pair for this session on this ordered VTEP pair. Per session: the SPI folds the
    VNI in, so concurrent sessions between the same nodes get distinct SAs."""
    key = _aead_key(key_hex)
    spi_out = f"{_esp_spi(vni, self_vtep, peer_vtep):#x}"
    spi_in = f"{_esp_spi(vni, peer_vtep, self_vtep):#x}"
    aead = ["aead", "rfc4106(gcm(aes))", key, str(_ICV_BITS)]
    return [
        ["ip", "xfrm", "state", "add", "src", self_vtep, "dst", peer_vtep,
         "proto", "esp", "spi", spi_out, "mode", "transport", *aead],
        ["ip", "xfrm", "state", "add", "src", peer_vtep, "dst", self_vtep,
         "proto", "esp", "spi", spi_in, "mode", "transport", *aead],
    ]  # fmt: skip


def xfrm_policy_add_args(
    self_vtep: str, peer_vtep: str, *, dstport: int = VXLAN_DSTPORT
) -> list[list[str]]:
    """The out/in policies selecting this node<->peer VXLAN UDP for ESP.

    NOT per session, and it cannot be: the selector is the OUTER packet (src/dst IP, udp dport) and
    the VNI lives inside the UDP payload, where no XFRM selector can reach it. So every session
    between the same two nodes on the same port shares one policy — which is why the caller
    refcounts it instead of deleting it with whichever session ends first. (See the SA args above:
    the SAs *are* per session, and both ends pick one by the SPI in the packet.)
    """
    return [
        ["ip", "xfrm", "policy", "update", "src", self_vtep, "dst", peer_vtep,
         "proto", "udp", "dport", str(dstport), "dir", "out",
         "tmpl", "src", self_vtep, "dst", peer_vtep, "proto", "esp", "mode", "transport"],
        ["ip", "xfrm", "policy", "update", "src", peer_vtep, "dst", self_vtep,
         "proto", "udp", "dport", str(dstport), "dir", "in",
         "tmpl", "src", peer_vtep, "dst", self_vtep, "proto", "esp", "mode", "transport"],
    ]  # fmt: skip


def xfrm_state_del_args(self_vtep: str, peer_vtep: str, vni: int) -> list[list[str]]:
    spi_out = f"{_esp_spi(vni, self_vtep, peer_vtep):#x}"
    spi_in = f"{_esp_spi(vni, peer_vtep, self_vtep):#x}"
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
         "proto", "udp", "dport", str(dstport), "dir", "out"],
        ["ip", "xfrm", "policy", "del", "src", peer_vtep, "dst", self_vtep,
         "proto", "udp", "dport", str(dstport), "dir", "in"],
    ]  # fmt: skip


def xfrm_add_args(
    self_vtep: str, peer_vtep: str, vni: int, key_hex: str, *, dstport: int = VXLAN_DSTPORT
) -> list[list[str]]:
    """The `ip xfrm` commands that encrypt this node↔peer VXLAN traffic: an out/in ESP SA pair plus
    the out/in policy selecting the VXLAN UDP.

    The states use `add`, not `update`: `XFRM_MSG_UPDSA` looks the SA up first and returns ESRCH
    when it is absent, so `update` alone never *creates* one -- measured, every call failed with
    "RTNETLINK answers: No such process" and the overlay ran in clear text while still paying the
    38-byte ESP MTU cost. `add` is EEXIST on an SA that survived an agent restart, which
    `_run_xfrm` handles by replaying it as `update`. Policies keep `update`, which is a true
    upsert (`XFRM_MSG_UPDPOLICY` creates when absent).
    """
    return [
        *xfrm_state_add_args(self_vtep, peer_vtep, vni, key_hex),
        *xfrm_policy_add_args(self_vtep, peer_vtep, dstport=dstport),
    ]


def xfrm_del_args(
    self_vtep: str, peer_vtep: str, vni: int, *, dstport: int = VXLAN_DSTPORT
) -> list[list[str]]:
    return [
        *xfrm_state_del_args(self_vtep, peer_vtep, vni),
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


async def _run_command(argv: Sequence[str]) -> None:
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed (rc={proc.returncode}): {' '.join(argv)}: "
            f"{stderr.decode(errors='replace').strip()}"
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
    # Peers whose ESP SA/policy pair this node has programmed, per session. XFRM lives in the
    # netns rather than on the device, so teardown has to unprogram it explicitly and cannot rely
    # on `del_peer` having run for every peer first.
    _encrypted_peers: dict[str, set[str]]
    # Which sessions are relying on the ESP policy for a given (self VTEP, peer VTEP, port). The
    # policy selector is the outer packet and carries nothing per session, so every session between
    # the same two nodes shares ONE policy; deleting it with whichever session ends first drops the
    # others to clear text, silently. Keyed by session id rather than counted so add/remove stay
    # idempotent under the coordinator's retries.
    _policy_users: dict[tuple[str, str, int], set[str]]
    # Per-session background reach probes, so teardown does not leave them running against a
    # bridge that is being deleted.
    _reach_tasks: dict[str, set[asyncio.Task[None]]]

    def __init__(
        self,
        plugin_config: Any,
        local_config: Any,
        *,
        uplink: str = "eth0",
        runner: Runner | None = None,
        local_subnets: LocalSubnetAllocator | None = None,
        mtu_probe: MtuProbe | None = None,
        reach_probe: ReachProbe | None = None,
    ) -> None:
        super().__init__(plugin_config, local_config)
        self._uplink = uplink
        self._runner = runner or _run_command
        # Injectable for the same reason as `runner`: the probe shells out and reads sysfs, and the
        # command builders must stay testable without either.
        self._mtu_probe = mtu_probe or underlay_mtu
        self._reach_probe = reach_probe or arp_probe
        self._reach_tasks = {}
        self._encrypted_peers = {}
        self._policy_users = {}
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
        pass

    @override
    async def cleanup(self) -> None:
        pass

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

    async def _del_forward_accept(self, vni: int) -> None:
        try:
            await self._runner(forward_accept_del_args(vni))
        except (RuntimeError, OSError):
            pass  # never installed, already gone, or no iptables

    @override
    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        if meta.backend is not NetworkBackendKind.VXLAN or meta.vni is None:
            raise ValueError(f"VxlanNetworkPlugin requires a vxlan meta with a VNI: {meta}")
        vni = meta.vni
        # Preconditions, so they run before any side effect: a session this node cannot carry must
        # leave nothing half-built behind.
        await self._require_mtu_fits(meta)
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
        await self._runner(
            vxlan_link_add_args(vni, self._uplink, mtu=meta.mtu, dstport=meta.vxlan_port)
        )
        await self._runner(bridge_link_add_args(vni, mtu=meta.mtu))
        await self._runner(set_master_args(vni))
        await self._runner(link_up_args(vxlan_dev(vni)))
        await self._runner(link_up_args(bridge_dev(vni)))
        await self._ensure_forward_accept(vni)
        self._sessions[meta.session_id] = meta
        if self_member.vtep_ip is not None:
            self._self_vteps[meta.session_id] = self_member.vtep_ip

    @override
    async def adopt_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        if meta.backend is not NetworkBackendKind.VXLAN or meta.vni is None:
            raise ValueError(f"VxlanNetworkPlugin requires a vxlan meta with a VNI: {meta}")
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
        self._sessions[meta.session_id] = meta
        if self_member.vtep_ip is not None:
            self._self_vteps[meta.session_id] = self_member.vtep_ip

    @override
    async def teardown_session_network(self, session_id: str) -> None:
        meta = self._sessions.pop(session_id, None)
        self_vtep = self._self_vteps.pop(session_id, None)
        peers = self._encrypted_peers.pop(session_id, set())
        for task in self._reach_tasks.pop(session_id, set()):
            task.cancel()
        # Read the index BEFORE releasing it: the release makes it unfindable, and the device it
        # names is deleted below. Read, not allocate -- teardown of a session this node never set
        # up must not mint an index and then delete the bridge that index names.
        local_index = await self._local_subnets.lookup(session_id)
        await self._local_subnets.release(session_id)
        if meta is None or meta.vni is None:
            return
        # XFRM lives in the netns, not on the device: deleting the vxlan link below leaves any SA
        # and policy behind. `del_peer` cannot be relied on to have run for every peer first --
        # a peer node can vanish, or teardown can win the race -- and a leftover SA is actively
        # harmful rather than untidy: the SPI is derived from (vni, src, dst), so the next session
        # that reuses the VNI on the same VTEP pair computes the SAME SPI with a DIFFERENT key and
        # its traffic is dropped. Measured: one node kept `SAD 2 / SPD 1+1` pointing at a dead peer
        # and the next encrypted session on that pair saw 100% loss until an `ip xfrm state flush`.
        for peer_vtep in sorted(peers):
            await self._unprogram_encryption(meta, session_id, peer_vtep, self_vtep)
        await self._del_forward_accept(meta.vni)
        # delete the overlay bridge/vxlan and the per-session LOCAL bridge; ignore missing.
        # `bailo<vni>` is the transitional name (see setup) and is removed alongside.
        devs = [bridge_dev(meta.vni), vxlan_dev(meta.vni), local_bridge_dev(meta.vni)]
        if local_index is not None:
            devs.insert(2, local_bridge_dev(local_index))
        for dev in devs:
            try:
                await self._runner(link_del_args(dev))
            except RuntimeError:
                log.debug("link {} already gone during teardown of {}", dev, session_id)

    @override
    async def add_peer(self, session_id: str, peer: Member) -> None:
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None or peer.vtep_ip is None:
            return
        await self._runner(fdb_append_args(meta.vni, peer.vtep_ip))
        # Encrypt this node↔peer VXLAN with kernel ESP (overlay-encryption.md). Program it beside the
        # FDB so the SA pair exists before any tunnel frame flows; the crypto is the kernel's.
        await self._program_encryption(meta, session_id, peer.vtep_ip)

    async def _program_encryption(
        self, meta: SessionNetMeta, session_id: str, peer_vtep: str
    ) -> None:
        if meta.encryption_key is None or meta.vni is None:
            return
        self_vtep = self._self_vteps.get(session_id)
        if self_vtep is None:
            # setup_session_network refuses an encrypted session on a node with no VTEP, so this
            # is only reachable for a session adopted before that check existed.
            log.warning(
                "cannot encrypt overlay for session {}: this node's VTEP is unknown", session_id
            )
            return
        # Recorded BEFORE the commands run, not after. A failure partway leaves SAs installed, and
        # an unrecorded SA is never unprogrammed -- the SPI is derived from (vni, src, dst), so the
        # next session that reuses the VNI on this VTEP pair computes the same SPI with a different
        # key and its traffic is dropped wholesale. Over-recording costs one best-effort delete;
        # under-recording costs a dead overlay.
        self._encrypted_peers.setdefault(session_id, set()).add(peer_vtep)
        for args in xfrm_state_add_args(self_vtep, peer_vtep, meta.vni, meta.encryption_key):
            await self._run_xfrm(args)
        users = self._policy_users.setdefault((self_vtep, peer_vtep, meta.vxlan_port), set())
        first = not users
        users.add(session_id)
        if first:
            for args in xfrm_policy_add_args(self_vtep, peer_vtep, dstport=meta.vxlan_port):
                await self._runner(args)

    async def _unprogram_encryption(
        self, meta: SessionNetMeta, session_id: str, peer_vtep: str, self_vtep: str | None
    ) -> None:
        """Remove this session's ESP SA pair, and the shared policy once nobody is left on it.

        Best-effort and idempotent. The SAs are this session's (the SPI folds the VNI in) and go
        unconditionally; the policy belongs to every session between the same two nodes on the same
        port, so it goes only when the last of them does. Deleting it with the first session to end
        is what silently drops the others to clear text -- they keep running, their SAs are still
        there, and nothing selects them any more.
        """
        if meta.encryption_key is None or meta.vni is None or self_vtep is None:
            self._encrypted_peers.get(session_id, set()).discard(peer_vtep)
            return
        for args in xfrm_state_del_args(self_vtep, peer_vtep, meta.vni):
            try:
                await self._runner(args)
            except RuntimeError:
                log.debug("xfrm state already gone for peer {} in {}", peer_vtep, session_id)
        key = (self_vtep, peer_vtep, meta.vxlan_port)
        users = self._policy_users.get(key, set())
        users.discard(session_id)
        if not users:
            self._policy_users.pop(key, None)
            for args in xfrm_policy_del_args(self_vtep, peer_vtep, dstport=meta.vxlan_port):
                try:
                    await self._runner(args)
                except RuntimeError:
                    log.debug("xfrm policy already gone for peer {}", peer_vtep)
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
        await self._unprogram_encryption(
            meta, session_id, peer.vtep_ip, self._self_vteps.get(session_id)
        )
        try:
            await self._runner(fdb_del_args(meta.vni, peer.vtep_ip))
        except RuntimeError:
            log.debug("fdb entry for {} already gone in session {}", peer.vtep_ip, session_id)

    @override
    async def add_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        """Proactively program a remote endpoint: unicast MAC→VTEP FDB + permanent ARP.

        Idempotent (``replace``). Known unicast then never floods over the tunnel."""
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None:
            return
        await self._runner(fdb_replace_args(meta.vni, mac, vtep_ip))
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
        # Bound here, not inside the closure: the guard above narrows `meta.vni` only in this
        # scope, and a nested function would read it as `int | None` again.
        bridge = bridge_dev(meta.vni)

        async def _run() -> None:
            for attempt in range(1, _REACH_ATTEMPTS + 1):
                answered = await self._reach_probe(bridge, ip, mac)
                if answered is None:
                    log.debug("overlay reach probe unavailable on {}; skipping", bridge)
                    return
                if answered:
                    log.debug(
                        "overlay reach probe: {} answered over {} (attempt {})",
                        ip,
                        bridge,
                        attempt,
                    )
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

        task = asyncio.create_task(_run())
        tasks = self._reach_tasks.setdefault(session_id, set())
        tasks.add(task)
        task.add_done_callback(tasks.discard)

    @override
    async def del_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None:
            return
        for argv in (fdb_del_args(meta.vni, vtep_ip, mac=mac), neigh_del_args(meta.vni, ip)):
            try:
                await self._runner(argv)
            except RuntimeError:
                log.debug("endpoint entry {} already gone in session {}", ip, session_id)

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
