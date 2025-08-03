"""
Agent selector interface for sokovan scheduler.

This module defines the interface for agent selection that abstracts away
the row-based implementation details of the legacy selectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Sequence

from ai.backend.common.types import AgentId, ResourceSlot, SessionId, SessionTypes


@dataclass
class AgentInfo:
    """Essential information about an agent for selection."""

    # Unique identifier of the agent
    agent_id: AgentId
    # Network address of the agent
    agent_addr: str
    # Architecture of the agent (e.g., "x86_64", "aarch64")
    architecture: str
    # Available resource slots on the agent
    available_slots: ResourceSlot
    # Currently occupied resource slots
    occupied_slots: ResourceSlot
    # Scaling group the agent belongs to
    scaling_group: str
    # Number of containers currently running on the agent
    container_count: int


@dataclass
class AgentSelectionCriteria:
    """Criteria for selecting an agent."""

    # Resource slots requested
    requested_slots: ResourceSlot
    # Required architecture (e.g., "x86_64", "aarch64")
    required_architecture: str
    # Scaling group name
    scaling_group: str
    # Maximum number of containers allowed per agent (None means no limit)
    max_container_count: Optional[int] = None
    # Specific agent to use (for manual assignment by superadmin)
    designated_agent_id: Optional[AgentId] = None
    # Session ID (needed for endpoint replica spreading in inference sessions)
    session_id: Optional[SessionId] = None
    # Session type (needed to determine if endpoint spreading applies)
    session_type: Optional[SessionTypes] = None
    # Whether to enforce endpoint replica spreading (from sgroup_opts)
    enforce_spreading_endpoint_replica: bool = False
    # Kernel counts at endpoint for each agent (for concentrated selector spreading)
    kernel_counts_at_endpoint: Optional[dict[AgentId, int]] = None


class AbstractAgentSelector(ABC):
    """
    Abstract base class for agent selection strategies.

    Subclasses should implement the strategy-specific selection logic.
    """

    @abstractmethod
    def select_agent_by_strategy(
        self,
        agents: Sequence[AgentInfo],
        criteria: AgentSelectionCriteria,
    ) -> Optional[AgentId]:
        """
        Select an agent using the specific strategy.

        This method should implement the core selection logic without
        handling designated agents or common filtering.

        Args:
            agents: Pre-filtered compatible agents
            criteria: Selection requirements

        Returns:
            The ID of the selected agent, or None if no suitable agent found
        """
        raise NotImplementedError


class AgentSelector:
    """
    Base agent selector with common logic.

    This class handles common concerns like designated agent selection,
    architecture filtering, resource availability checking, and container limit filtering.
    """

    _strategy: AbstractAgentSelector

    def __init__(self, strategy: AbstractAgentSelector) -> None:
        self._strategy = strategy

    async def select_agent(
        self,
        agents: Sequence[AgentInfo],
        criteria: AgentSelectionCriteria,
    ) -> Optional[AgentId]:
        """
        Select an agent from the available agents based on the selection criteria.

        Handles common logic before delegating to the strategy-specific implementation.

        Args:
            agents: Available agents to choose from
            criteria: Selection requirements and hints

        Returns:
            The ID of the selected agent, or None if no suitable agent found
        """
        # Handle designated agent if specified
        if criteria.designated_agent_id:
            for agent in agents:
                if agent.agent_id == criteria.designated_agent_id:
                    # Verify the designated agent meets all requirements
                    if not self._is_agent_compatible(agent, criteria):
                        return None
                    return criteria.designated_agent_id
            return None

        # Filter agents by compatibility
        compatible_agents = [
            agent for agent in agents if self._is_agent_compatible(agent, criteria)
        ]

        if not compatible_agents:
            return None

        # Delegate to strategy for selection
        return self._strategy.select_agent_by_strategy(compatible_agents, criteria)

    def _is_agent_compatible(self, agent: AgentInfo, criteria: AgentSelectionCriteria) -> bool:
        """Check if an agent is compatible with the selection criteria."""
        # Check architecture compatibility
        if agent.architecture != criteria.required_architecture:
            return False

        # Check resource availability
        available_slots = agent.available_slots - agent.occupied_slots
        if not (available_slots >= criteria.requested_slots):
            return False

        # Check container limit if specified
        if criteria.max_container_count is not None:
            if agent.container_count >= criteria.max_container_count:
                return False

        return True
