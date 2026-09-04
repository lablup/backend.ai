"""Cluster-session network exceptions (BEP-1062)."""

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
    """An explicitly requested cluster-network subnet is not usable as-is (BEP-1062).

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
    """An explicitly requested subnet overlaps an already-allocated block (BEP-1062).

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


class ForcedBackendUnsupported(BackendAIError, web.HTTPBadRequest):
    """The operator pinned a data-plane backend that cannot serve a multi-node session (BEP-1062).

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
    """A member agent is not CNI-capable while the network driver is 'cni' (BEP-1062).

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
