"""
Resource slot domain exceptions.
"""

from __future__ import annotations

from typing import override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class ResourceSlotTypeNotFound(BackendAIError):
    """Raised when a requested resource slot type does not exist."""

    error_type = "https://api.backend.ai/probs/resource-slot-type-not-found"
    error_title = "Resource slot type not found."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ResourceSlotTypeAlreadyExists(BackendAIError):
    """Raised when creating a resource slot type whose slot name is already registered."""

    error_type = "https://api.backend.ai/probs/resource-slot-type-already-exists"
    error_title = "Resource slot type already exists."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class ResourceSlotTypeInUse(BackendAIError):
    """Raised when deleting a resource slot type that is still referenced elsewhere."""

    error_type = "https://api.backend.ai/probs/resource-slot-type-in-use"
    error_title = "Resource slot type is still referenced."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class AgentResourceNotFound(BackendAIError):
    """Raised when an agent resource entry for a given agent+slot is not found."""

    error_type = "https://api.backend.ai/probs/agent-resource-not-found"
    error_title = "Agent resource not found."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ResourceAllocationNotFound(BackendAIError):
    """Raised when a resource allocation entry for a given kernel+slot is not found."""

    error_type = "https://api.backend.ai/probs/resource-allocation-not-found"
    error_title = "Resource allocation not found."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AgentResourceCapacityExceeded(BackendAIError):
    """Raised when an agent resource update would exceed the slot capacity."""

    error_type = "https://api.backend.ai/probs/agent-resource-capacity-exceeded"
    error_title = "Agent resource capacity exceeded."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )
