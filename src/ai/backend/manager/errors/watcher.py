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


class WatcherTokenNotConfigured(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when etcd config/watcher/token is not set."""

    error_type = "https://api.backend.ai/probs/watcher-token-not-configured"
    error_title = "The agent watcher token is not configured."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.WATCHER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.NOT_READY,
        )
