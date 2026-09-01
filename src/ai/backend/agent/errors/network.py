"""
Cluster-network exceptions for the agent (BEP-1062).
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class LocalSubnetPoolExhausted(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when every node-local /24 block for session LOCAL bridges is taken."""

    error_type = "https://api.backend.ai/probs/agent/local-subnet-pool-exhausted"
    error_title = "No free node-local subnet is available for the session LOCAL bridge."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class LocalSubnetSourceUnwired(BackendAIError, web.HTTPInternalServerError):
    """The session network was built with no way to look up a session's LOCAL subnet.

    Exactly one source is correct: this process's own journal when it owns the node's pool, or an
    RPC to the privnet when the privnet owns it. With neither, ``local_subnet_of`` answers None for
    every session, which reads as "no block claimed" — so single-node peer layout silently loses
    its addresses and the cluster resolver refuses to start. Raise where the wiring is decided,
    not several layers down where the symptom appears.
    """

    error_type = "https://api.backend.ai/probs/agent/local-subnet-source-unwired"
    error_title = "The session network has no source for node-local subnet lookups."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class LocalSubnetLayoutChanged(BackendAIError, web.HTTPInternalServerError):
    """The node-local pool was re-cut while sessions still hold blocks from the old one.

    A journalled index names a subnet only against the pool it was cut from, so reading it back
    under a different pool (or block size) would name a subnet the live bridge is not on. The
    operator has to drain the node before changing either.
    """

    error_type = "https://api.backend.ai/probs/agent/local-subnet-layout-changed"
    error_title = "The node-local subnet pool changed while sessions still hold blocks from it."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class OverlayAddressNotAssigned(BackendAIError, web.HTTPInternalServerError):
    """The manager did not assign an overlay IP for a multi-node vxlan endpoint.

    The overlay subnet is stretched across the cluster, so a node cannot pick an address locally
    without colliding with its peers. A missing assignment is a control-plane bug; fail loudly
    rather than attach a colliding address.
    """

    error_type = "https://api.backend.ai/probs/agent/overlay-address-not-assigned"
    error_title = "No manager-assigned overlay address for the cluster-network endpoint."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class SubnetAddressPoolExhausted(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when a host-local subnet has no free address left for a container endpoint."""

    error_type = "https://api.backend.ai/probs/agent/subnet-address-pool-exhausted"
    error_title = "No free address is available in the container subnet."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class SessionNetworkGone(BackendAIError, web.HTTPInternalServerError):
    """A kernel reached for its session's network on this node and it was not there.

    The kernels of a session are created in stages and concurrently, so this names the case where
    the session was torn down while this kernel was still being built on top of it.
    """

    error_type = "https://api.backend.ai/probs/agent/session-network-gone"
    error_title = "The session's network is not set up on this node."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class StaticAddressUnavailable(BackendAIError, web.HTTPInternalServerError):
    """A container could not be pinned at the specific address its peers expect.

    A single-node cluster's peers resolve each other through a deterministic address map, so a
    kernel that cannot take its own address is worse than a kernel that fails: the map would name
    an address nothing answers on. Fail the kernel instead.
    """

    error_type = "https://api.backend.ai/probs/agent/static-address-unavailable"
    error_title = "The requested container address is not available in the subnet."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class UnusableVtep(BackendAIError, web.HTTPInternalServerError):
    """This node cannot anchor a vxlan tunnel, so it must not join a multi-node overlay session.

    The VTEP is what peers program into their FDB. Publishing one that is empty, unspecified or
    not held by this host yields an overlay that comes up, reports no error and carries no traffic
    — the failure then surfaces as a hang at rendezvous, far from its cause. Refuse the session on
    this node instead, naming the setting to fix.
    """

    error_type = "https://api.backend.ai/probs/agent/unusable-vtep"
    error_title = "This agent has no usable VTEP address for a multi-node overlay session."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class OverlayEncryptionUnavailable(BackendAIError, web.HTTPInternalServerError):
    """Raised when a session asks for an encrypted overlay this node cannot encrypt.

    The ESP SAs are keyed on the ordered VTEP pair, so a node with no usable tunnel endpoint has no
    `src` to program them with. Running anyway is the failure worth refusing: the session comes up,
    carries traffic, and is in clear text on the wire with only a log line to say so.
    """

    error_type = "https://api.backend.ai/probs/agent/overlay-encryption-unavailable"
    error_title = "Overlay encryption cannot be programmed on this node."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class OverlayMtuTooLarge(BackendAIError, web.HTTPInternalServerError):
    """The overlay MTU the manager computed does not fit this node's real underlay.

    The manager derives it from a configured underlay constant, not from a measurement, so any
    pod network that encapsulates (flannel vxlan/ipip/wireguard, calico vxlan/ipip, cilium tunnel)
    leaves the overlay exactly its own overhead too large. Nothing reports that: small packets
    pass, full-size frames are dropped with no ICMP, and the session hangs later in bulk transfer
    with no hint of why. Refusing here, naming the measured value to configure, is the same trade
    `UnusableVtep` makes -- a loud failure beats a silent one.

    Clamping locally would be worse than refusing: each node would clamp to its own path and the
    two ends of one tunnel would disagree, so the larger side's frames would vanish in exactly the
    way this guard exists to prevent.
    """

    error_type = "https://api.backend.ai/probs/agent/overlay-mtu-too-large"
    error_title = "The session's overlay MTU exceeds what this node's underlay can carry."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class PortForwardError(BackendAIError, web.HTTPInternalServerError):
    """Raised when installing or removing a container's host-port DNAT rule fails."""

    error_type = "https://api.backend.ai/probs/agent/port-forward-error"
    error_title = "Failed to publish the container's service port on a host port."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ClusterDNSStartError(BackendAIError, web.HTTPInternalServerError):
    """The per-session cluster DNS resolver could not be bound.

    Peers resolve through this resolver — the static ``/etc/hosts`` peer map was removed in favour
    of it (cluster-name-resolution.md, phase 5). So a resolver that fails to start leaves cluster
    hostnames unresolvable, and the session would hang at rendezvous with no visible cause. Fail the
    kernel loudly here instead of coming up silently broken.
    """

    error_type = "https://api.backend.ai/probs/agent/cluster-dns-start-error"
    error_title = "Failed to start the session's cluster DNS resolver."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NetworkStateStoreConflict(BackendAIError, web.HTTPInternalServerError):
    """A network state store on disk disagrees with its owner's in-memory state.

    Each store has exactly one writer per node, so a record the owner believes is free but which
    already exists on disk means a second writer is mutating this node's network — a condition the
    data plane cannot survive anyway (session setup deletes and recreates host devices by name).
    Fail loudly rather than allocate over it.
    """

    error_type = "https://api.backend.ai/probs/agent/network-state-store-conflict"
    error_title = "The on-disk network state store was modified by another writer."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )
