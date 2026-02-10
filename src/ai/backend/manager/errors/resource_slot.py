"""
Resource slot domain exceptions.
"""

from __future__ import annotations

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

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AgentResourceCapacityExceeded(BackendAIError):
    """Raised when an agent resource update would exceed the slot capacity."""

    error_type = "https://api.backend.ai/probs/agent-resource-capacity-exceeded"
    error_title = "Agent resource capacity exceeded."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )
