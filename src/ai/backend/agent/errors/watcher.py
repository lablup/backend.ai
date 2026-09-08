"""
Agent watcher-related exceptions.
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


class InvalidWatcherTokenError(BackendAIError, web.HTTPForbidden):
    """Raised when the request does not carry the configured watcher token."""

    error_type = "https://api.backend.ai/probs/agent/invalid-watcher-token"
    error_title = "Invalid watcher token."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.WATCHER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )
