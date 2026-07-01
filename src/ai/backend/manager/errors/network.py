"""Cluster-session network exceptions (BEP-1055)."""

from __future__ import annotations

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

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class VNIPoolExhausted(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/vni-pool-exhausted"
    error_title = "No free VNI is available in the cluster-network VNI range."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
