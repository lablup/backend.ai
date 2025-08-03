"""Agent selector interfaces and implementations for sokovan scheduler."""

from .exceptions import (
    AgentSelectionError,
    DesignatedAgentIncompatibleError,
    DesignatedAgentNotFoundError,
    NoAvailableAgentError,
    NoCompatibleAgentError,
)
from .selector import (
    AbstractAgentSelector,
    AgentInfo,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentSelector,
    ResourceRequirements,
    SessionMetadata,
)

__all__ = [
    # Exceptions
    "AgentSelectionError",
    "DesignatedAgentIncompatibleError",
    "DesignatedAgentNotFoundError",
    "NoAvailableAgentError",
    "NoCompatibleAgentError",
    # Core interfaces
    "AbstractAgentSelector",
    "AgentInfo",
    "AgentSelectionConfig",
    "AgentSelectionCriteria",
    "AgentSelector",
    "ResourceRequirements",
    "SessionMetadata",
]
