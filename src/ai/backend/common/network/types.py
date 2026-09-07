"""Runtime-neutral data types for cluster-session networking.

These types decouple the cluster-network control plane and data-plane backends
from any specific container runtime (Docker, containerd, ...). See
proposals/BEP-1078 and its sub-documents `control-plane.md` and `agent-plugin-v2.md`.
"""

from __future__ import annotations

import ipaddress
import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Final

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# --- tunnel constants, shared by the manager (which computes the overlay MTU) and the agent
# (which builds the devices and checks the result against the real path) ---

DEFAULT_VXLAN_PORT = 4789
"""The IANA VXLAN port, and the default this project ships.

It is a *default*, not a constant, because a cluster's CNI may already claim it in a way that is
fatal to us. Calico programs an anti-spoofing rule on the host side of every pod veth --
``-A cali-fw-<iface> -p udp -m multiport --dports <felix vxlanPort> -j DROP``, commented "Drop
VXLAN encapped packets originating in workloads" -- whose port is Felix's ``vxlanPort``, also 4789
by default. It is installed regardless of Calico's own encapsulation mode (measured: it fires with
Calico in IPIP mode, where Calico uses no VXLAN at all), so on a Calico cluster a session overlay
on 4789 comes up and carries nothing. Moving either side off 4789 restores it.
"""

DEFAULT_VNI_RANGE = (4096, 16777215)

#: The VXLAN VNI is a 24-bit field. This is the wire's range, not the allocator's: a VNI outside
#: what an operator configured the pool to hand out is unusual, but a VNI outside THIS is not a
#: VNI at all.
VNI_MIN, VNI_MAX = 1, (1 << 24) - 1

#: What an overlay MTU may be. Below the IPv4 minimum reassembly buffer nothing can be relied on
#: to arrive; above the largest jumbo frame no NIC in the path will carry it.
MTU_MIN, MTU_MAX = 576, 9000
#: The VXLAN service port must be unprivileged: the agent binds it, and a privileged one would
#: have the overlay contend with a listener the node already trusts.
VXLAN_PORT_MIN, VXLAN_PORT_MAX = 1024, 65535

#: The only address space a session overlay is ever carved from. Both sides check it: the agent
#: because the manager's value reaches `ip` as an argument, the manager because a record naming a
#: subnet from outside it is a record it should not act on.
PRIVATE_POOLS: Final = (
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
)


def reads_as_vni(value: Any) -> int | None:
    """``value`` as a VXLAN VNI, or None if it is not one.

    Strict about the type, not just about `int()`. ``bool`` is an ``int`` subclass and ``int()``
    truncates a float, so ``true`` and ``1.5`` would both become segment identifiers nobody chose
    -- and on the manager side, a value read as a VNI it is not is a value that makes a live
    session's real VNI look unclaimed.
    """
    if isinstance(value, (bool, float)) or not isinstance(value, (int, str)):
        return None
    try:
        vni = int(value)
    except (TypeError, ValueError):
        return None
    return vni if VNI_MIN <= vni <= VNI_MAX else None


def reads_as_overlay_subnet(value: Any) -> str | None:
    """``value`` as a session overlay subnet, or None if it is not one.

    IPv4, inside `PRIVATE_POOLS`, and aligned to its own prefix. A session block is claimed and
    released by CIDR string, so a value that is a network but not one of these is not something
    either side can act on.
    """
    if not isinstance(value, str):
        return None
    try:
        net = ipaddress.ip_network(value, strict=True)
    except ValueError:
        return None
    if not isinstance(net, ipaddress.IPv4Network):
        return None
    return value if any(net.subnet_of(pool) for pool in PRIVATE_POOLS) else None


"""The VNI pool the manager allocates from, and the range an agent checks a foreign tunnel
against. Starts above the 0-4095 a hand-configured tunnel is most likely to use; the top is the
24-bit VNI maximum."""

VXLAN_OVERHEAD = 50
"""IPv4 VXLAN encapsulation: 20 IP + 8 UDP + 8 VXLAN + 14 inner Ethernet."""

ESP_OVERHEAD = 38
"""Transport-mode ESP/AES-GCM added on top of VXLAN when overlay encryption is on: 8 ESP header
(SPI + seq) + 8 IV + 16 ICV + up to 6 pad/trailer. See overlay-encryption.md."""

SESSION_META_STATE: Final = "_state"
"""Where the manager records how far a session's network record got.

Absent on a record an agent wrote for its own single-node session; on the manager's, anything but
``SESSION_META_READY`` is a session still being built or being undone, whose subnet and VNI are
not committed to anybody."""

SESSION_META_READY: Final = "ready"
"""The one value of ``SESSION_META_STATE`` that means the record may be acted on."""

SESSION_META_GENERATION: Final = "generation"
"""Where the manager records WHICH incarnation of a session id a record, a claim or a key belongs
to.

A session id is reused: a session torn down and started again under the same id gets a fresh
subnet, VNI and endpoints, and every key of the old one is indistinguishable from the new one's by
name alone. The generation is minted once, when the record is created out of nothing, and carried
unchanged by everything that incarnation writes -- pool claims, endpoints, the per-session IPAM
reservations and each node's member record -- so a cleanup, a late agent join or a superseded
create can tell its own incarnation from the one that replaced it. See
`CNINetworkPlugin._finish_cleanup` and `SessionNetworkCoordinator._session_fence`."""


def of_generation(raw: str, generation: str | None) -> bool:
    """Whether a record carrying ``raw`` may be acted on by a call working for ``generation``.

    True for a record of that same incarnation, and for one carrying no generation at all -- what
    a component from before the field wrote, and what nothing else will ever come back for. False
    for one stamped with a DIFFERENT incarnation: that belongs to the session which replaced the
    one being cleaned up, and it is live. Unreadable is False -- a value this cannot parse is not
    one it may claim to own.

    See ``SESSION_META_GENERATION``.
    """
    try:
        record = json.loads(raw)
    except ValueError:
        return False
    if not isinstance(record, Mapping):
        # Valid JSON that is not an object -- ``null``, ``[]``, a bare number. ``.get`` on it
        # raises AttributeError, which is not what any caller here catches, so one such key under
        # a session stopped every reconciliation that reached it: on the agent, the session's
        # whole membership pass, every fifteen seconds, for as long as the key stood.
        return False
    stamped = record.get(SESSION_META_GENERATION)
    return stamped is None or stamped == generation


def mac_for_ip(ip: str) -> str:
    """Derive a stable, locally-administered unicast MAC from an IPv4 address.

    Uses the ``02:42:`` prefix (locally-administered, unicast — the same convention Docker
    uses) followed by the four IPv4 octets, so the MAC is unique per endpoint IP and
    deterministic. This is the SINGLE source of truth both sides share: the manager programs
    peers' FDB/ARP to this MAC and the agent sets the container's overlay NIC to the same
    MAC, so they agree without a round-trip. If they diverged, a peer's unicast frame
    (dst=02:42:...) would not match the container NIC's address and be dropped.
    """
    octets = ipaddress.IPv4Address(ip).packed
    return "02:42:" + ":".join(f"{b:02x}" for b in octets)


class NetworkBackendKind(StrEnum):
    """Selectable data-plane backends for a cluster-session network."""

    VXLAN = "vxlan"
    """VXLAN overlay. Portable default; per-session isolation via VNI."""
    BRIDGE = "bridge"
    """Node-local per-session bridge with no cross-node overlay. Used for single-node
    sessions: a plain CNI bridge (host-local IPAM) gives the container a host-reachable IP,
    replacing the former nerdctl-managed bridge."""


class AttachKind(StrEnum):
    """How a runtime should attach a container to a session network."""

    CNI = "cni"
    """CNI runtimes (containerd, ...): apply ``cni_config`` to the container netns."""
    DOCKER_NETWORK = "docker"
    """Docker runtime (v1 back-compat): merge ``docker_config`` into the create request."""
    HOST_NETNS = "netns"
    """Agent-driven veth/setns using ``netns_ops``."""


class NetworkRole(StrEnum):
    """Purpose of a single interface attached to a container."""

    LOCAL = "local"
    """Host-local bridge. Always present. The host (agent) is this bridge's gateway, so it
    doubles as (1) the agent<->container control channel and (2) external egress via NAT.
    Inter-container communication is disabled (egress-only between containers) so a shared
    per-node bridge cannot bridge two different sessions; host<->container still works.
    Carries the container's default route."""
    OVERLAY = "overlay"
    """Cross-node cluster network. Present only for multi-node sessions. Exactly one L2
    domain = the session; carries inter-node isolation. Installs only the session-subnet route."""


@dataclass(frozen=True)
class SessionNetMeta:
    """Source-of-truth network descriptor for one cluster session.

    Written by the manager under ``network/session/{session_id}/meta`` and consumed
    by every data-plane backend.
    """

    session_id: str
    subnet: str
    backend: NetworkBackendKind
    mtu: int
    vni: int | None = None
    """VXLAN Network Identifier; set only when ``backend == VXLAN``."""
    vxlan_port: int = DEFAULT_VXLAN_PORT
    """UDP port this session's VXLAN tunnel uses, on the wire and in the XFRM policy selector.

    Carried in the meta rather than read from each agent's own config so the two ends of a tunnel
    cannot disagree -- a one-sided change yields an overlay that comes up and carries nothing.
    See ``DEFAULT_VXLAN_PORT`` for why an operator would move it off 4789.
    """
    encryption_key: str | None = None
    """Hex-encoded 256-bit cluster root for kernel IPSec (ESP/AES-GCM) traffic-key derivation, or
    ``None`` for a plaintext overlay -- which a VXLAN session is only when something asked for it,
    since the manager encrypts by default (see `CNINetworkPlugin._encryption_enabled`). The root is
    distributed via etcd like ``vni``; the backend derives pair-and-12-hour-generation keys and
    programs only those into XFRM. See overlay-encryption.md."""
    generation: str | None = None
    """Which incarnation of ``session_id`` this descriptor names -- see ``SESSION_META_GENERATION``.

    ``None`` on a single-node BRIDGE meta the agent writes for itself, and on one from a manager
    older than the field."""


@dataclass(frozen=True)
class Member:
    """A node participating in a session network.

    Each agent writes its own entry under ``network/session/{session_id}/members/{agent_id}``.
    """

    agent_id: str
    host_ip: str
    vtep_ip: str | None = None
    """VXLAN tunnel endpoint address; used by the vxlan backend for FDB entries."""
    joined: bool = False
    """Whether the AGENT wrote this record, rather than the manager pre-seeding it.

    The two look alike and mean opposite things at teardown. A pre-seed says "this node is
    *expected* to take part" and is written before the node has touched anything; a self-publish
    says "this node holds host state for the session". Only the second is an acknowledgement, so
    only the second may hold the session's VNI back from reuse.
    """
    generation: str | None = None
    """Which incarnation of the session this membership is of -- see ``SESSION_META_GENERATION``.

    A session id is reused, so a member key alone does not say which of its incarnations wrote it.
    Carrying the generation is what lets a cleanup delete its own incarnation's membership without
    reaching the one a node published for the session that replaced it."""

    def to_etcd_payload(self) -> dict[str, str | bool | None]:
        """The member's etcd value (``agent_id`` is the key, not part of the value).

        Single source of the on-wire member schema — used by both the agent (self-publish)
        and the manager (pre-seed) so the two never drift."""
        return {
            "host_ip": self.host_ip,
            "vtep_ip": self.vtep_ip,
            "joined": self.joined,
            "generation": self.generation,
        }

    @classmethod
    def from_etcd_payload(cls, agent_id: str, payload: Mapping[str, Any]) -> Member:
        return cls(
            agent_id=agent_id,
            host_ip=payload["host_ip"],
            vtep_ip=payload.get("vtep_ip"),
            # A record written before this field existed came from an agent: the manager's
            # pre-seed is newer than the field, so the older shape can only be a self-publish.
            joined=bool(payload.get("joined", True)),
            generation=payload.get("generation"),
        )


@dataclass(frozen=True)
class EndpointAddr:
    """A manager-assigned overlay address for one container endpoint.

    Written by the manager under ``network/session/{session_id}/endpoints/{container_id}``
    and consumed by overlay backends: the CNI attach uses ``ip`` (static IPAM) and the
    coordinator proactively programs FDB + neighbor (ARP) entries from ``ip``/``mac``/
    ``agent_id`` — no per-node host-local allocation, no BUM flood.

    ``cluster_hostname`` (``main1``, ``sub1``, …) makes this table the session-scoped
    ``hostname -> ip`` source the per-session cluster name resolver reads (BEP-1078,
    cluster-name-resolution.md) — the same per-session ``endpoints/`` prefix, so names never
    share a global namespace and cannot collide across sessions.
    """

    container_id: str
    ip: str
    mac: str
    agent_id: str
    cluster_hostname: str | None = None
    """The kernel's in-cluster hostname. ``None`` only for endpoints written before this field
    existed (backward-compatible decode); a name-less endpoint is simply not resolvable by name."""
    generation: str | None = None
    """Which incarnation of the session this endpoint belongs to -- see
    ``SESSION_META_GENERATION``. What lets a cleanup delete its own incarnation's endpoints and
    leave the ones a later session built under the same id."""

    def to_etcd_payload(self) -> dict[str, str | None]:
        """The endpoint's etcd value (``container_id`` is the key, but kept in the value too for
        the coordinator's reverse lookups). Single source of the on-wire schema — used by the
        manager (assign) and the agent (decode) so the two never drift."""
        return {
            "ip": self.ip,
            "mac": self.mac,
            "agent_id": self.agent_id,
            "container_id": self.container_id,
            "cluster_hostname": self.cluster_hostname,
            "generation": self.generation,
        }

    @classmethod
    def from_etcd_payload(cls, container_id: str, payload: Mapping[str, Any]) -> EndpointAddr:
        return cls(
            container_id=container_id,
            ip=payload["ip"],
            mac=payload["mac"],
            agent_id=payload["agent_id"],
            cluster_hostname=payload.get("cluster_hostname"),
            generation=payload.get("generation"),
        )


@dataclass(frozen=True)
class NetworkAttachSpec:
    """Runtime-neutral description of how to attach ONE interface to a container.

    Exactly one of ``cni_config`` / ``docker_config`` / ``netns_ops`` is populated,
    matching ``kind``. The runtime-specific provisioner interprets it. A container may
    receive several of these as an ordered chain (see ``EndpointPlan``): always one LOCAL
    interface, plus one OVERLAY interface for multi-node sessions.
    """

    kind: AttachKind
    interface_name: str
    role: NetworkRole = NetworkRole.LOCAL
    is_default_route: bool = False
    """Whether this interface carries the container's default route. Typically the
    LOCAL interface; the OVERLAY interface installs only the session-subnet route."""
    ip: str | None = None
    """Preassigned address, when known. May be None when the interface's IPAM
    (e.g. host-local for the LOCAL interface) assigns it at attach time."""
    cni_config: Mapping[str, Any] | None = None
    cni_capability_args: Mapping[str, Any] | None = None
    """Standard CNI capability args (e.g. ``{"ips": ["10.0.0.5/26"], "mac": "02:.."}``). The
    provisioner injects each one into ``runtimeConfig`` for the capability its ``cni_config``
    declares under ``capabilities`` — the standard way to pin a specific IP / MAC, replacing the
    non-standard ``ipam.requested_ip`` / top-level ``mac`` keys a real CNI binary would ignore."""
    docker_config: Mapping[str, Any] | None = None
    netns_ops: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class EndpointPlan:
    """Ordered set of interfaces to attach to one container.

    Invariants (enforced by backends, not the dataclass):
      - Exactly one attachment has ``role == LOCAL`` (agent control + egress).
      - Multi-node sessions additionally have exactly one ``role == OVERLAY``.
      - At most one attachment has ``is_default_route == True`` (normally the LOCAL one).
    """

    attachments: list[NetworkAttachSpec]

    def local(self) -> NetworkAttachSpec:
        """Return the single always-present LOCAL attachment."""
        return next(a for a in self.attachments if a.role is NetworkRole.LOCAL)

    def overlay(self) -> NetworkAttachSpec | None:
        """Return the OVERLAY attachment for multi-node sessions, or None for single-node."""
        return next((a for a in self.attachments if a.role is NetworkRole.OVERLAY), None)


class OverlayEncryptionPolicy(StrEnum):
    """What an operator means by asking for overlay encryption.

    A boolean could not hold both "encrypt this" and "encrypt this if you can", so it meant the
    weaker one for everybody: an operator who wrote `true` because these sessions are confidential
    was handed plain VXLAN and a log line the moment one agent turned out to be old.
    """

    #: Encrypt, and refuse the session if any node it lands on cannot. The default.
    REQUIRED = "required"
    #: Encrypt where every node can; fall back to plain VXLAN, loudly, where they cannot. For a
    #: cluster mid-upgrade, chosen deliberately.
    PREFER = "prefer"
    #: Never encrypt.
    DISABLED = "disabled"

    @classmethod
    def parse(cls, value: Any) -> OverlayEncryptionPolicy:
        """The policy an operator's configuration asks for, defaulting to `REQUIRED`.

        Booleans are accepted because that is what this setting used to be: `true` is `REQUIRED`
        and `false` is `DISABLED`, which is what each meant to whoever wrote it. An unrecognised
        value is `REQUIRED` too -- a typo in a security setting must not be read as permission.
        """
        if value is None:
            return cls.REQUIRED
        if isinstance(value, bool):
            return cls.REQUIRED if value else cls.DISABLED
        try:
            return cls(str(value).strip().lower())
        except ValueError:
            log.warning(
                "unrecognised overlay-encryption policy {!r}; using {!r}", value, cls.REQUIRED.value
            )
            return cls.REQUIRED


#: The wire contract of an encrypted overlay: transport-mode ESP with AES-GCM, extended sequence
#: numbers, and traffic keys derived per node pair and generation.
#:
#: Named and versioned because the two ends of a tunnel must agree on ALL of it. An agent from
#: before ESN cannot decrypt what one with it sends, so a session that mixes them comes up and
#: carries nothing -- which is what a rolling upgrade produces the moment encryption stops being
#: something an operator opted into node by node. The manager refuses to encrypt a session unless
#: every node it lands on publishes this exact string.
#:
#: Bump it when the derivation, the algorithm or the replay handling changes, so that a mixed
#: cluster fails at placement with a reason instead of at first packet without one.
OVERLAY_ENCRYPTION_PROFILE: Final = "esp-aesgcm-esn-v1"


@dataclass(frozen=True)
class AgentNetworkCaps:
    """Per-agent networking capabilities used by the control plane to select a backend.

    Published under ``network/agent/{agent_id}/caps``.
    """

    tunnel_offload: bool
    backends: list[str] = field(default_factory=list)
    #: What would stop this node from serving an overlay session, in the operator's words; empty
    #: when nothing would. Published rather than enforced: the node still refuses a session it
    #: cannot protect when one arrives, and that guard belongs in the data-plane backend. This is
    #: so the reason is visible BEFORE a session is scheduled here and fails on one node.
    readiness: list[str] = field(default_factory=list)
    #: The overlay encryption profiles this node can hold up ITS end of. Absent -- which is what an
    #: agent from before this field publishes -- means none: see `OVERLAY_ENCRYPTION_PROFILE`.
    encryption_profiles: list[str] = field(default_factory=list)
