"""Cluster-session network exceptions (BEP-1078)."""

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


class NetworkPoolExhausted(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/network-pool-exhausted"
    error_title = "No free subnet is available in the cluster-network IPAM pool."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class VNIPoolExhausted(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/vni-pool-exhausted"
    error_title = "No free VNI is available in the cluster-network VNI range."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class RequestedSubnetInvalid(BackendAIError, web.HTTPBadRequest):
    """An explicitly requested cluster-network subnet is not usable as-is (BEP-1078).

    Raised before any allocation for a subnet that is malformed, has host bits set (not aligned
    to its own prefix), is not contained in the IPAM pool, or is narrower than one unit block
    (``ipam-block-size``) — the granularity the pool is accounted at.
    """

    error_type = "https://api.backend.ai/probs/requested-subnet-invalid"
    error_title = "The requested cluster-network subnet is invalid for this IPAM pool."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class RequestedSubnetUnavailable(BackendAIError, web.HTTPConflict):
    """An explicitly requested subnet overlaps an already-allocated block (BEP-1078).

    Unlike auto-allocation (which skips a taken block and tries the next), an explicit request
    names a specific range, so an overlap is a hard failure — as ``docker network create --subnet``
    fails rather than relocating.
    """

    error_type = "https://api.backend.ai/probs/requested-subnet-unavailable"
    error_title = "The requested cluster-network subnet overlaps an allocated block."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class OverlayTeardownPending(BackendAIError, web.HTTPInternalServerError):
    """A node still holds the session's overlay state, so its VNI cannot be reused yet.

    Not an error in the sense that something went wrong -- it is the normal shape of a node that
    is a beat slower than the manager. It is raised rather than returned because the caller
    retries on failure and on nothing else: returning quietly would release the VNI, the subnet
    and the session's keys the moment one node lagged, and hand that VNI to a session that would
    then inherit the laggard's devices and rules.
    """

    error_type = "https://api.backend.ai/probs/overlay-teardown-pending"
    error_title = "The session's overlay allocation is still held by one of its nodes."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ForcedBackendUnsupported(BackendAIError, web.HTTPBadRequest):
    """The operator pinned a data-plane backend that cannot serve a multi-node session (BEP-1078).

    The CNI control plane only ever provisions multi-node cluster sessions, whose IPs are
    assigned centrally and stretched across nodes over an overlay. The 'bridge' backend is
    node-local (single-node) and ignores the manager's central IPAM, so pinning it here would
    hand every node an /etc/hosts full of overlay addresses no container actually holds. Only
    'vxlan' (or leaving 'forced-backend' unset) is valid here.
    """

    error_type = "https://api.backend.ai/probs/forced-backend-unsupported"
    error_title = "The pinned cluster-network backend cannot serve a multi-node session."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class NetworkBackendMismatch(BackendAIError, web.HTTPConflict):
    """A member agent is not CNI-capable while the network driver is 'cni' (BEP-1078).

    This guards the deployment invariant that the agent backend (docker/containerd) and the
    global network driver (overlay/cni) must be a matched pair — a multi-node session
    cannot span nodes on different network fabrics.
    """

    error_type = "https://api.backend.ai/probs/network-backend-mismatch"
    error_title = "Agent network backend does not match the cluster network driver."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class SubnetClaimStranded(BackendAIError, web.HTTPInternalServerError):
    """A partial subnet claim could not be given back, so those unit blocks are stranded.

    Failed rather than passed over: no meta names them and no release ever will.
    """

    error_type = "https://api.backend.ai/probs/manager/subnet-claim-stranded"
    error_title = "A partial IPAM claim could not be released."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class SessionCleanupPending(BackendAIError, web.HTTPConflict):
    """A previous network for this session is still being cleaned up.

    Retryable: building over keys and an allocation something else is still deleting is not.
    """

    error_type = "https://api.backend.ai/probs/manager/session-network-cleanup-pending"
    error_title = "The session's previous network has not finished being removed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class EndpointSuperseded(BackendAIError, web.HTTPConflict):
    """This create's endpoint write would have landed on another incarnation of the session.

    A session id is reused. A create stalled long enough for its session to be torn down and built
    again resumes holding the old subnet and the old generation, and the endpoint record it writes
    is what every peer programs FDB and ARP from. Refused rather than written, so the stale create
    unwinds instead of pointing the live session's peers at addresses nothing holds.

    Retryable: the retry reads the record that is actually there.
    """

    error_type = "https://api.backend.ai/probs/manager/session-endpoint-superseded"
    error_title = "The session's endpoint record belongs to a later incarnation."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class SessionRecordContested(BackendAIError, web.HTTPConflict):
    """Another manager took this session's network record while a create was running.

    Retryable: the session is somebody's, and the next attempt reads what they published.
    """

    error_type = "https://api.backend.ai/probs/manager/session-network-record-contested"
    error_title = "The session's network record belongs to another manager."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class ManagerNetworkMisconfigured(BackendAIError, web.HTTPInternalServerError):
    """An overlay setting no session built from it could be attached.

    Every one of these values travels to the agent, whose privnet policy is the trust boundary and
    refuses an MTU or a port outside its ranges and a subnet outside RFC1918. Checked when the
    plugin starts or its config changes rather than inside a create, because by then the create
    has claimed the session and would publish a READY record over a descriptor no node can use --
    a healthy-looking session that never attaches, and a retry that rebuilds the same one.

    Not retryable: an operator has to change the setting.
    """

    error_type = "https://api.backend.ai/probs/manager/network-misconfigured"
    error_title = "The cluster network plugin is configured with a value no agent can accept."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
