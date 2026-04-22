"""
Stats streaming-related exceptions.
"""

from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class ContainerStatsStreamError(BackendAIError, web.HTTPInternalServerError):
    """Raised when the long-lived container stats stream fails after exhausting retries."""

    error_type = "https://api.backend.ai/probs/agent/container-stats-stream-failed"
    error_title = "Container stats stream failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
