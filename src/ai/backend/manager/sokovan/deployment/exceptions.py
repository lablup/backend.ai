"""Exceptions for deployment operations."""

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class DeploymentError(BackendAIError):
    """Base exception for deployment errors."""

    error_type = "https://api.backend.ai/probs/deployment-failed"
    error_title = "Deployment operation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ModelVFolderNotFound(DeploymentError):
    """Raised when model vfolder is not found."""

    error_type = "https://api.backend.ai/probs/model-vfolder-not-found"
    error_title = "Model vfolder not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InvalidVFolderOwnership(DeploymentError):
    """Raised when vfolder has invalid ownership type."""

    error_type = "https://api.backend.ai/probs/invalid-vfolder-ownership"
    error_title = "Cannot use project type vfolder as model."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class GroupNotFound(DeploymentError):
    """Raised when group/project is not found."""

    error_type = "https://api.backend.ai/probs/group-not-found"
    error_title = "Group or project not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DuplicateEndpointName(DeploymentError):
    """Raised when endpoint name already exists."""

    error_type = "https://api.backend.ai/probs/duplicate-endpoint-name"
    error_title = "Endpoint name already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class ImageNotFound(DeploymentError):
    """Raised when image cannot be resolved."""

    error_type = "https://api.backend.ai/probs/image-not-found"
    error_title = "Image not found or cannot be resolved."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class EndpointNotFound(DeploymentError):
    """Raised when endpoint is not found."""

    error_type = "https://api.backend.ai/probs/endpoint-not-found"
    error_title = "Endpoint not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ServiceInfoRetrievalFailed(DeploymentError):
    """Raised when service info retrieval fails."""

    error_type = "https://api.backend.ai/probs/service-info-retrieval-failed"
    error_title = "Failed to retrieve service information."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
