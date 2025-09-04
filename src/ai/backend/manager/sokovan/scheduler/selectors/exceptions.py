"""
Exceptions for agent selection in sokovan scheduler.
"""

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import AgentId, ResourceSlot
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
    error_title = "Unavailable : No agents can be allocated at this time."

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


# Tracker compatibility check exceptions (not inheriting from SchedulingError)
class TrackerCompatibilityError(Exception):
    """Base exception for tracker compatibility checks."""

    pass


class ArchitectureIncompatibleError(TrackerCompatibilityError):
    """Raised when agent architecture does not match the required architecture."""

    def __init__(self, agent_id: AgentId, agent_arch: str, required_arch: str) -> None:
        self.agent_id = agent_id
        self.agent_arch = agent_arch
        self.required_arch = required_arch
        super().__init__(
            f"Agent {agent_id} architecture '{agent_arch}' does not match required architecture '{required_arch}'"
        )


class InsufficientResourcesError(TrackerCompatibilityError):
    """Raised when agent does not have sufficient resources available."""

    def __init__(
        self,
        agent_id: AgentId,
        requested_slots: ResourceSlot,
        available_slots: ResourceSlot,
        occupied_slots: ResourceSlot,
        insufficient_resources: dict[str, tuple[str, str]],
    ) -> None:
        self.agent_id = agent_id
        self.requested_slots = requested_slots
        self.available_slots = available_slots
        self.occupied_slots = occupied_slots
        self.insufficient_resources = insufficient_resources

        # Build detailed message showing which resources are insufficient
        resource_details = []
        for resource_name, (requested, available) in insufficient_resources.items():
            resource_details.append(
                f"{resource_name}: requested={requested}, available={available}"
            )
        details_msg = "; ".join(resource_details)

        super().__init__(f"Agent {agent_id} has insufficient resources: {details_msg}")


class ContainerLimitExceededError(TrackerCompatibilityError):
    """Raised when agent has reached its maximum container count limit."""

    def __init__(
        self,
        agent_id: AgentId,
        current_count: int,
        max_count: int,
    ) -> None:
        self.agent_id = agent_id
        self.current_count = current_count
        self.max_count = max_count
        super().__init__(
            f"Agent {agent_id} container limit exceeded: current={current_count}, max={max_count}"
        )
