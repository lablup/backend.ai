"""
Exceptions for agent selection in sokovan scheduler.
"""

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class AgentSelectionError(BackendAIError):
    """Base exception for agent selection errors."""

    error_type = "https://api.backend.ai/probs/agent-selection-failed"
    error_title = "Agent selection failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NoAvailableAgentError(AgentSelectionError):
    """Raised when no agents are available."""

    error_type = "https://api.backend.ai/probs/no-available-agents"
    error_title = "No agents are available for selection."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class DesignatedAgentNotFoundError(AgentSelectionError):
    """Raised when designated agent is not found."""

    error_type = "https://api.backend.ai/probs/designated-agent-not-found"
    error_title = "Designated agent not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DesignatedAgentIncompatibleError(AgentSelectionError):
    """Raised when designated agent doesn't meet requirements."""

    error_type = "https://api.backend.ai/probs/designated-agent-incompatible"
    error_title = "Designated agent does not meet resource requirements."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.MISMATCH,
        )


class NoCompatibleAgentError(AgentSelectionError):
    """Raised when no compatible agents are found."""

    error_type = "https://api.backend.ai/probs/no-compatible-agents"
    error_title = "No agents meet the resource requirements."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class NoResourceRequirementsError(AgentSelectionError):
    """Raised when no resource requirements are found for a session."""

    error_type = "https://api.backend.ai/probs/no-resource-requirements"
    error_title = "No resource requirements found for session."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
