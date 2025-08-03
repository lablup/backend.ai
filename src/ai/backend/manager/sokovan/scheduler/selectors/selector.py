"""
Agent selector interface for sokovan scheduler.

This module defines the interface for agent selection that abstracts away
the row-based implementation details of the legacy selectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence
from uuid import UUID

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes


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
class SessionMetadata:
    """Metadata for the session being scheduled."""

    # Session ID
    session_id: SessionId
    # Type of the session (e.g., INTERACTIVE, BATCH, INFERENCE)
    session_type: SessionTypes
    # Scaling group the session belongs to
    scaling_group: str
    # Cluster mode (e.g., SINGLE, MULTI)
    cluster_mode: ClusterMode


@dataclass
class AgentSelectionConfig:
    """Configuration for agent selection."""

    # Maximum number of containers allowed per agent
    max_container_count: Optional[int]
    # Whether to enforce endpoint replica spreading (from sgroup_opts)
    enforce_spreading_endpoint_replica: bool = False


@dataclass
class ResourceRequirements:
    """Resource requirements for allocation."""

    # Resource slots required
    requested_slots: ResourceSlot
    # Architecture required
    required_architecture: str


@dataclass
class AgentSelectionCriteria2:
    """Criteria for selecting an agent."""

    # Session metadata for the selection
    session_metadata: SessionMetadata
    # Kernel requirements for the session
    # Mapping of kernel IDs to their resource requirements
    kernel_requirements: Mapping[UUID, ResourceRequirements]
    # Kernel counts at endpoint for each agent (for concentrated selector spreading)
    kernel_counts_at_endpoint: Optional[Mapping[AgentId, int]] = None

    def get_resource_requirements(self) -> Sequence[ResourceRequirements]:
        """
        Get all resource requirements for the session's kernels.

        For single-node sessions, returns a sequence with one element containing
        the aggregated resource requirements for all kernels.

        For multi-node sessions, returns a sequence with each kernel's resource
        requirements separately.

        Returns:
            A list of ResourceRequirements for the session.

        Raises:
            ValueError: If single-node session has kernels with different architectures.
        """
        if self.session_metadata.cluster_mode == ClusterMode.SINGLE_NODE:
            # Check architecture consistency for single-node
            architectures = {
                kernel_req.required_architecture for kernel_req in self.kernel_requirements.values()
            }
            if len(architectures) > 1:
                raise ValueError(
                    f"Single-node session has kernels with different architectures: {architectures}"
                )

            # Sum all requested slots for single-node sessions
            total_slots = ResourceSlot({})
            for kernel_req in self.kernel_requirements.values():
                total_slots = total_slots + kernel_req.requested_slots

            # Use the common architecture
            architecture = next(iter(architectures)) if architectures else "x86_64"
            return [
                ResourceRequirements(
                    requested_slots=total_slots, required_architecture=architecture
                )
            ]
        else:
            # Return individual kernel resources for multi-node sessions
            return list(self.kernel_requirements.values())


class AbstractAgentSelector(ABC):
    """
    Abstract base class for agent selection strategies.

    Subclasses should implement the strategy-specific selection logic.
    """

    @abstractmethod
    def select_agent_by_strategy(
        self,
        agents: Sequence[AgentInfo],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria2,
        config: AgentSelectionConfig,
    ) -> Optional[AgentId]:
        """
        Select an agent using the strategy with specific resource requirements.

        This method should implement the core selection logic without
        handling designated agents or common filtering.

        Args:
            agents: Pre-filtered compatible agents
            resource_req: Resource requirements to satisfy
            criteria: Selection criteria including session metadata
            config: Configuration for agent selection

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

    async def select_agent_for_kernel(
        self,
        agents: Sequence[AgentInfo],
        criteria: AgentSelectionCriteria2,
        config: AgentSelectionConfig,
        kernel_id: UUID,
        designated_agent: Optional[AgentId] = None,
    ) -> Optional[AgentId]:
        """
        Select an agent for a specific kernel based on the selection criteria.

        Handles common logic before delegating to the strategy-specific implementation.

        Args:
            agents: Available agents to choose from
            criteria: Selection requirements including session metadata and kernel requirements
            config: Configuration for agent selection
            kernel_id: ID of the kernel being scheduled
            designated_agent: Manually designated agent (for superadmin)

        Returns:
            The ID of the selected agent, or None if no suitable agent found
        """
        # Get kernel requirements
        kernel_req = criteria.kernel_requirements.get(kernel_id)
        if not kernel_req:
            return None

        # Handle designated agent if specified
        if designated_agent:
            for agent in agents:
                if agent.agent_id == designated_agent:
                    # Verify the designated agent meets all requirements
                    if not self._is_agent_compatible(agent, kernel_req, config):
                        return None
                    return designated_agent
            return None

        # Filter agents by compatibility
        compatible_agents = [
            agent for agent in agents if self._is_agent_compatible(agent, kernel_req, config)
        ]

        if not compatible_agents:
            return None

        # Delegate to strategy for selection
        return self._strategy.select_agent_by_strategy(
            compatible_agents, kernel_req, criteria, config
        )

    async def select_agent_for_resource_requirements(
        self,
        agents: Sequence[AgentInfo],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria2,
        config: AgentSelectionConfig,
        designated_agent: Optional[AgentId] = None,
    ) -> Optional[AgentId]:
        """
        Select an agent for given resource requirements.

        Args:
            agents: Available agents to choose from
            resource_req: Resource requirements to satisfy
            criteria: Selection criteria (for metadata like session type)
            config: Configuration for agent selection
            designated_agent: Manually designated agent (for superadmin)

        Returns:
            The ID of the selected agent, or None if no suitable agent found
        """
        if not agents:
            return None
        # Handle designated agent if specified
        if designated_agent:
            for agent in agents:
                if agent.agent_id == designated_agent:
                    # Verify the designated agent meets all requirements
                    if not self._is_agent_compatible(agent, resource_req, config):
                        return None
                    return designated_agent
            return None

        # Filter agents by compatibility
        compatible_agents = [
            agent for agent in agents if self._is_agent_compatible(agent, resource_req, config)
        ]

        if not compatible_agents:
            return None

        # For strategy selection, we need to pass the resource requirements
        return self._strategy.select_agent_by_strategy(
            compatible_agents, resource_req, criteria, config
        )

    def _is_agent_compatible(
        self,
        agent: AgentInfo,
        resource_req: ResourceRequirements,
        config: AgentSelectionConfig,
    ) -> bool:
        """Check if an agent is compatible with the resource requirements."""
        # Check architecture compatibility
        if agent.architecture != resource_req.required_architecture:
            return False

        # Check resource availability
        available_slots = agent.available_slots - agent.occupied_slots
        if not (available_slots >= resource_req.requested_slots):
            return False

        # Check container limit if specified
        if config.max_container_count is not None:
            if agent.container_count >= config.max_container_count:
                return False

        return True
