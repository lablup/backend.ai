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


class UnsupportedNetworkBackend(BackendAIError, web.HTTPBadRequest):
    """The selected cluster-network backend has no agent-side implementation (BEP-1062).

    host-gw and wireguard are declared in NetworkBackendKind for the selection interface but are
    not implemented. Refusing them here — whether pinned by the operator's forced_backend or
    reached by capability auto-selection — turns a late agent-side UnknownNetworkBackend crash into
    a clear create-time error.
    """

    error_type = "https://api.backend.ai/probs/unsupported-network-backend"
    error_title = "The selected cluster-network backend is not implemented."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )
