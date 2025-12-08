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
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ResourceAllocationError(BackendAIError, web.HTTPInternalServerError):
    """Raised when resource allocation fails due to internal error."""

    error_type = "https://api.backend.ai/probs/agent/resource-allocation-error"
    error_title = "Resource allocation error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.MISMATCH,
        )


class InvalidOvercommitFactorError(BackendAIError, web.HTTPBadRequest):
    """Raised when overcommit factor is out of valid range."""

    error_type = "https://api.backend.ai/probs/agent/invalid-overcommit-factor"
    error_title = "Invalid overcommit factor."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidAllocMapTypeError(BackendAIError, web.HTTPInternalServerError):
    """Raised when allocation map type is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-alloc-map-type"
    error_title = "Invalid allocation map type."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.MISMATCH,
        )


class InvalidMeasurementError(BackendAIError, web.HTTPInternalServerError):
    """Raised when measurement data is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-measurement"
    error_title = "Invalid measurement data."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.MISMATCH,
        )


class InvalidConfigFormatError(BackendAIError, web.HTTPBadRequest):
    """Raised when configuration format is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-config-format"
    error_title = "Invalid configuration format."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class InvalidContainerMeasurementError(BackendAIError, web.HTTPInternalServerError):
    """Raised when container measurement type is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-container-measurement"
    error_title = "Invalid container measurement type."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )
