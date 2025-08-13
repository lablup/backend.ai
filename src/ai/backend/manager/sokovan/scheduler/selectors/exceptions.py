"""
Exceptions for agent selection in sokovan scheduler.
"""

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.sokovan.scheduler.exceptions import SchedulingError
from ai.backend.manager.sokovan.scheduler.types import SchedulingPredicate


class AgentSelectionError(SchedulingError):
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

    def failed_predicates(self) -> list[SchedulingPredicate]:
        """Return list of failed predicates for this error."""
        return [SchedulingPredicate(name=type(self).__name__, msg=str(self))]


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
