"""Runtime-neutral data types for cluster-session networking.

These types decouple the cluster-network control plane and data-plane backends
from any specific container runtime (Docker, containerd, ...). See
proposals/BEP-1055 and its sub-documents `control-plane.md` and `agent-plugin-v2.md`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class NetworkBackendKind(StrEnum):
    """Selectable data-plane backends for a cluster-session network."""

    VXLAN = "vxlan"
    """VXLAN overlay. Portable default; per-session isolation via VNI."""
    HOST_GW = "host-gw"
    """Native L3 routing without encapsulation; requires a cooperative fabric."""
    WIREGUARD = "wireguard"
    """Encrypted host-to-host tunnels; use when confidentiality is required."""


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


@dataclass(frozen=True)
class Member:
    """A node participating in a session network.

    Each agent writes its own entry under ``network/session/{session_id}/members/{agent_id}``.
    """

    agent_id: str
    host_ip: str
    vtep_ip: str | None = None
    """VXLAN tunnel endpoint address; used by the vxlan backend for FDB entries."""
    ip_range: str | None = None
    """Sub-range of the session subnet owned by this node; used by the host-gw backend."""


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


@dataclass(frozen=True)
class AgentNetworkCaps:
    """Per-agent networking capabilities used by the control plane to select a backend.

    Published under ``network/agent/{agent_id}/caps``.
    """

    tunnel_offload: bool
    native_routing_ok: bool
    backends: list[str] = field(default_factory=list)
