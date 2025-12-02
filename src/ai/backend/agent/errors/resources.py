"""
Resource-related exceptions for the agent.
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


class InvalidResourceConfigError(BackendAIError, web.HTTPBadRequest):
    """Raised when resource configuration is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-resource-config"
    error_title = "Invalid resource configuration."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AgentIdNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when the agent ID is not found in the configuration."""

    error_type = "https://api.backend.ai/probs/agent/agent-id-not-found"
    error_title = "Agent ID not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ResourceOverAllocatedError(BackendAIError, web.HTTPBadRequest):
    """Raised when resources are over-allocated beyond their limit."""

    error_type = "https://api.backend.ai/probs/agent/resource-over-allocated"
    error_title = "Resources are over-allocated."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
