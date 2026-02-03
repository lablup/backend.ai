"""
Fair share domain exceptions.
"""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class FairShareError(BackendAIError):
    """Base class for fair share domain errors."""

    error_type = "https://api.backend.ai/probs/fair-share-error"
    error_title = "Fair share operation failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class FairShareNotFoundError(FairShareError):
    """Raised when a fair share entity is not found."""

    error_type = "https://api.backend.ai/probs/fair-share-not-found"
    error_title = "Fair share entity not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InvalidResourceWeightError(FairShareError):
    """Raised when resource_weights contains resource types not available in capacity."""

    error_type = "https://api.backend.ai/probs/invalid-resource-weight"
    error_title = "Invalid resource weight configuration."

    def __init__(self, invalid_types: list[str]) -> None:
        self.invalid_types = invalid_types
        super().__init__(f"Resource types not available in capacity: {', '.join(invalid_types)}")

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCALING_GROUP,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class DomainNotConnectedToResourceGroupError(FairShareError):
    """Raised when a domain is not connected to the specified resource group."""

    error_type = "https://api.backend.ai/probs/domain-not-connected-to-resource-group"
    error_title = "Domain is not connected to the resource group."

    def __init__(self, domain_name: str, resource_group: str) -> None:
        self.domain_name = domain_name
        self.resource_group = resource_group
        super().__init__(
            f"Domain '{domain_name}' is not connected to resource group '{resource_group}'."
        )

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ProjectNotConnectedToResourceGroupError(FairShareError):
    """Raised when a project is not connected to the specified resource group."""

    error_type = "https://api.backend.ai/probs/project-not-connected-to-resource-group"
    error_title = "Project is not connected to the resource group."

    def __init__(self, project_id: str, resource_group: str) -> None:
        self.project_id = project_id
        self.resource_group = resource_group
        super().__init__(
            f"Project '{project_id}' is not connected to resource group '{resource_group}'."
        )

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class UserNotConnectedToResourceGroupError(FairShareError):
    """Raised when a user is not connected to the specified resource group."""

    error_type = "https://api.backend.ai/probs/user-not-connected-to-resource-group"
    error_title = "User is not connected to the resource group."

    def __init__(self, user_uuid: str, project_id: str, resource_group: str) -> None:
        self.user_uuid = user_uuid
        self.project_id = project_id
        self.resource_group = resource_group
        super().__init__(
            f"User '{user_uuid}' in project '{project_id}' is not connected to "
            f"resource group '{resource_group}'."
        )

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )
