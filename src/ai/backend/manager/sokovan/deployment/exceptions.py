"""
Exceptions for deployment management.
"""

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class DeploymentError(BackendAIError):
    """Base exception for deployment-related errors."""

    error_type = "https://api.backend.ai/probs/deployment-failed"
    error_title = "Deployment operation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class InvalidEndpointState(DeploymentError):
    """Raised when an endpoint is in an invalid state for the requested operation."""

    error_type = "https://api.backend.ai/probs/invalid-endpoint-state"
    error_title = "Invalid endpoint state."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.BAD_REQUEST,  # Use BAD_REQUEST instead of INVALID_STATE
        )


class RouteCreationFailed(DeploymentError):
    """Raised when route creation fails."""

    error_type = "https://api.backend.ai/probs/route-creation-failed"
    error_title = "Failed to create route."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ScalingOperationFailed(DeploymentError):
    """Raised when a scaling operation fails."""

    error_type = "https://api.backend.ai/probs/scaling-failed"
    error_title = "Scaling operation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ServiceInfoRetrievalFailed(DeploymentError):
    """Raised when service info cannot be retrieved."""

    error_type = "https://api.backend.ai/probs/service-info-retrieval-failed"
    error_title = "Failed to retrieve service information."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
