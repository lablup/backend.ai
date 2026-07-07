"""Cluster-session network exceptions (BEP-1055)."""

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
    """A member agent is not CNI-capable while the network driver is 'cni' (BEP-1055).

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
