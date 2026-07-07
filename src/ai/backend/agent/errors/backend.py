"""
Compute-backend (instance lifecycle) exceptions for the agent.
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


class InstanceNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when an instance referenced by a handle no longer exists."""

    error_type = "https://api.backend.ai/probs/agent/instance-not-found"
    error_title = "Instance not found."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.INSTANCE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )
