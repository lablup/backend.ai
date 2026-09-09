"""
Cluster-network exceptions for the agent (BEP-1078).
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


class UnknownPrivnetBackend(BackendAIError, web.HTTPInternalServerError):
    """The privnet cannot tell which backend's containers it is meant to see.

    It answers three questions about containers (see ai.backend.agent.network.locator) through the
    client of whichever backend the agent runs. Guessing one is worse than refusing: a client for
    the wrong runtime reports "no such container" for every kernel the agent actually started, and
    every attach fails with nothing to point at.
    """

    error_type = "https://api.backend.ai/probs/agent/unknown-privnet-backend"
    error_title = "The privnet does not know which backend it serves."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class PrivnetConfigurationInvalid(BackendAIError, web.HTTPInternalServerError):
    """The privileged network daemon received an unsafe startup configuration."""

    error_type = "https://api.backend.ai/probs/agent/privnet-configuration-invalid"
    error_title = "The privnet startup configuration is invalid."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class PrivnetAlreadyRunning(BackendAIError, web.HTTPConflict):
    """Another process is accepting requests on the configured privnet socket."""

    error_type = "https://api.backend.ai/probs/agent/privnet-already-running"
    error_title = "Another privnet process is already running."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.CONFLICT,
        )


class UnsafePrivnetSocket(BackendAIError, web.HTTPInternalServerError):
    """The configured socket path cannot be replaced safely."""

    error_type = "https://api.backend.ai/probs/agent/unsafe-privnet-socket"
    error_title = "The privnet socket path is unsafe."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class HostAddressesUnreadable(BackendAIError, web.HTTPInternalServerError):
    """This node could not be asked which addresses it already carries.

    The node-local subnet allocator hands out a block only if nothing on the host already answers
    inside it: a leaked bridge, or one an agent still on the pre-node-wide code journalled where
    this allocator cannot see it. Reading the failure as "no addresses" handed that block out
    again, putting two bridges on one subnet with the same gateway -- which breaks quietly, on
    whichever container's traffic happens to take the wrong one.

    So the session is refused instead. Loud, and on the node that cannot answer for itself.
    """

    error_type = "https://api.backend.ai/probs/agent/host-addresses-unreadable"
    error_title = "This node's own addresses could not be read."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
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


class ContainerSourceUnwired(BackendAIError, web.HTTPInternalServerError):
    """The session network was built with nothing to ask about the node's containers.

    It needs two things, and they may be one object: a runtime for the container lifecycle (images,
    exec, kill) and a locator for the four questions the session half asks. The OCI-spec backends
    pass a runtime and get the locator derived from it; a backend that keeps its own lifecycle --
    Docker -- passes only a locator. Neither means every recovery reports an empty node, which
    reads as "nothing is running here" and tears down data planes that are still carrying traffic.
    """

    error_type = "https://api.backend.ai/probs/agent/container-source-unwired"
    error_title = "The session network has no source of container facts."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ContainerLifecycleUnavailable(BackendAIError, web.HTTPInternalServerError):
    """A container-lifecycle call was made on a session network that has no runtime.

    The backend that built it keeps its own lifecycle and only borrowed the session half; reaching
    these methods means something routed a Docker kernel's image pull or kill through the wrong
    object. Naming that beats an AttributeError on None several frames in.
    """

    error_type = "https://api.backend.ai/probs/agent/container-lifecycle-unavailable"
    error_title = "This session network does not drive a container runtime."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
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


class UndescribableVxlanDevice(BackendAIError, web.HTTPInternalServerError):
    """Another VXLAN is on this host and its parameters cannot be read.

    The plaintext-drop and mark rules select on (UDP port, VNI) and nothing else, so a co-tenant
    tunnel sharing both would have its frames dropped as unprotected plaintext, and its traffic
    marked for this session's XFRM policy -- in both directions, with neither side told. Refusing
    is the answer because the alternative is admitting on "could not check", which reads exactly
    like "checked, nothing there".
    """

    error_type = "https://api.backend.ai/probs/agent/undescribable-vxlan-device"
    error_title = (
        "A VXLAN device on this node cannot be described, so a collision cannot be ruled out."
    )

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class OverlayTeardownIncomplete(BackendAIError, web.HTTPInternalServerError):
    """Raised when teardown could not remove everything it owns on this node.

    Only "already absent" counts as removed. A permission error, a held xtables lock or an EBUSY
    device leaves real state behind -- SAs, policies, firewall rules, links -- and reporting that
    as success is what makes it permanent: the caller drops its record and nothing ever revisits
    it, while the manager hands the VNI to the next session that then inherits a stranger's rules.
    Raising keeps this node's ownership so teardown can be retried against the same session.
    """

    error_type = "https://api.backend.ai/probs/agent/overlay-teardown-incomplete"
    error_title = "The session's overlay state could not be fully removed on this node."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
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


class ContainerAttachFailed(BackendAIError, web.HTTPInternalServerError):
    """A container could not be wired into its session network.

    Not a cancelled one: an interrupted attach propagates as itself.
    """

    error_type = "https://api.backend.ai/probs/agent/container-attach-failed"
    error_title = "Failed to attach the container to its session network."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class InvalidSessionNetworkDescriptor(BackendAIError, web.HTTPInternalServerError):
    """The manager-provided session network descriptor cannot be applied."""

    error_type = "https://api.backend.ai/probs/agent/invalid-session-network-descriptor"
    error_title = "The session network descriptor is invalid."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class NetworkOperationFailed(BackendAIError, web.HTTPInternalServerError):
    """A host network operation failed without a more specific domain error."""

    error_type = "https://api.backend.ai/probs/agent/network-operation-failed"
    error_title = "A host network operation failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.EXECUTE,
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


class PrivilegedNetworkHelperFailed(BackendAIError, web.HTTPInternalServerError):
    """The privileged network helper refused or failed a request.

    A `BackendAIError` because it reaches session creation, and what arrives at the manager
    decides what an operator is told. A built-in `ConnectionRefusedError` carries errno 111 and
    nothing else -- not which node, not which socket, not that the whole data plane on that node
    is down rather than one operation having failed.
    """

    error_type = "https://api.backend.ai/probs/agent/privileged-network-helper-failed"
    error_title = "The privileged network helper could not carry out the request."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class PrivilegedNetworkHelperUnreachable(PrivilegedNetworkHelperFailed):
    """The helper could not be reached at all, rather than refusing one request.

    A subclass, so every caller that already degrades on a failed request keeps doing so; the
    distinction is for the ones that want to say why, and for readiness, which reports a node
    whose helper is down instead of letting each session discover it at create time.
    """

    error_type = "https://api.backend.ai/probs/agent/privileged-network-helper-unreachable"
    error_title = "The privileged network helper is not reachable on this node."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
