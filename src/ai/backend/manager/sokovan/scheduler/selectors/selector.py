"""
Agent selector interface for sokovan scheduler.

This module defines the interface for agent selection that abstracts away
the row-based implementation details of the legacy selectors.
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence
from uuid import UUID

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes

from .exceptions import (
    ContainerLimitExceededError,
    InsufficientResourcesError,
    NoAvailableAgentError,
    NoCompatibleAgentError,
)


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
class AgentStateTracker:
    """Tracks agent state changes during batch selection."""

    original_agent: AgentInfo
    additional_slots: ResourceSlot = field(default_factory=ResourceSlot)
    additional_containers: int = 0

    def get_current_occupied_slots(self) -> ResourceSlot:
        """Get current occupied slots (original + additional)."""
        return self.original_agent.occupied_slots + self.additional_slots

    def get_current_container_count(self) -> int:
        """Get current container count (original + additional)."""
        return self.original_agent.container_count + self.additional_containers

    def apply_diff(self, slots: ResourceSlot, containers: int) -> None:
        """Apply additional resource allocation."""
        self.additional_slots = self.additional_slots + slots
        self.additional_containers += containers


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
class KernelResourceSpec:
    """Resource specification for a single kernel."""

    # Resource slots required
    requested_slots: ResourceSlot
    # Architecture required
    required_architecture: str


@dataclass
class ResourceRequirements:
    """Resource requirements for allocation."""

    # Resource slots required
    requested_slots: ResourceSlot
    # Architecture required
    required_architecture: str
    # Kernel IDs that these requirements are for
    # For single-node, this includes all kernel IDs
    # For multi-node, this includes only one kernel ID
    kernel_ids: Sequence[UUID]


@dataclass
class AgentSelection:
    """Result of selecting an agent for specific resource requirements."""

    resource_requirements: ResourceRequirements
    selected_agent: AgentInfo


@dataclass
class AgentSelectionCriteria:
    """Criteria for selecting an agent."""

    # Session metadata for the selection
    session_metadata: SessionMetadata
    # Kernel requirements for the session
    # Mapping of kernel IDs to their resource specifications
    kernel_requirements: Mapping[UUID, KernelResourceSpec]
    # Kernel counts at endpoint for each agent (for concentrated selector spreading)
    kernel_counts_at_endpoint: Optional[Mapping[AgentId, int]] = None

    def get_resource_requirements(self) -> Sequence[ResourceRequirements]:
        """
        Get resource requirements based on cluster mode.

        For single-node sessions, returns a sequence with one aggregated requirement
        that includes all kernel IDs.
        For multi-node sessions, returns individual kernel requirements, each with
        its corresponding kernel ID.

        Returns:
            A sequence of ResourceRequirements.

        Raises:
            ValueError: If single-node session has kernels with different architectures.
        """
        if not self.kernel_requirements:
            # Return empty list for sessions with no kernels
            return []

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
            architecture = list(architectures)[0]
            # Include all kernel IDs in the aggregated requirement
            kernel_ids = list(self.kernel_requirements.keys())
            return [
                ResourceRequirements(
                    requested_slots=total_slots,
                    required_architecture=architecture,
                    kernel_ids=kernel_ids,
                )
            ]
        else:
            # Return individual kernel resources for multi-node sessions
            return [
                ResourceRequirements(
                    requested_slots=req.requested_slots,
                    required_architecture=req.required_architecture,
                    kernel_ids=[kernel_id],
                )
                for kernel_id, req in self.kernel_requirements.items()
            ]


class AbstractAgentSelector(ABC):
    """
    Abstract base class for agent selection strategies.

    Subclasses should implement the strategy-specific selection logic.
    """

    @abstractmethod
    def name(self) -> str:
        """
        Return the selector name for predicates.
        """
        raise NotImplementedError

    @abstractmethod
    def success_message(self) -> str:
        """
        Return a message describing successful agent selection.
        """
        raise NotImplementedError

    @abstractmethod
    def select_tracker_by_strategy(
        self,
        trackers: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
    ) -> AgentStateTracker:
        """
        Select an agent tracker using the strategy with specific resource requirements.

        This method should implement the core selection logic without
        handling designated agents or common filtering.

        Args:
            trackers: Pre-filtered compatible trackers (guaranteed non-empty)
            resource_req: Resource requirements to satisfy
            criteria: Selection criteria including session metadata
            config: Configuration for agent selection

        Returns:
            The selected tracker
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

    async def select_agents_for_batch_requirements(
        self,
        agents: Sequence[AgentInfo],
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        designated_agent_ids: Optional[list[AgentId]] = None,
    ) -> list[AgentSelection]:
        """
        Select agents for a batch of resource requirements.

        This method extracts resource requirements from criteria and processes
        them all at once, returning paired selections. Agent state changes are
        tracked internally as diffs and applied to the mutable agents list at the end.

        Args:
            agents: Available agents to choose from (will be modified with diff updates)
            criteria: Selection criteria including kernel requirements
            config: Configuration for agent selection
            designated_agent_ids: Optional list of designated agents for the session

        Returns:
            List of AgentSelection objects pairing requirements with selected agents

        Raises:
            NoAvailableAgentError: If no agents are available
            NoCompatibleAgentError: If no compatible agents are found
            ValueError: If architecture mismatch in single-node session
        """
        resource_requirements = criteria.get_resource_requirements()
        if not resource_requirements:
            # Return empty list for sessions with no kernels
            return []
        if not agents:
            raise NoAvailableAgentError(
                f"No agents available in scaling group '{criteria.session_metadata.scaling_group}'"
            )

        # Track agent state changes as diffs using AgentStateTracker
        state_trackers = [AgentStateTracker(original_agent=agent) for agent in agents]

        selections: list[AgentSelection] = []

        for resource_req in resource_requirements:
            # Select agent for this requirement using state trackers
            selected_tracker = await self._select_agent_tracker_for_requirements(
                state_trackers,
                resource_req,
                criteria,
                config,
                designated_agent_ids,
            )

            # Update state tracker with diff for the selected agent
            selected_tracker.apply_diff(resource_req.requested_slots, len(resource_req.kernel_ids))

            # Store the selection with the original agent
            selections.append(
                AgentSelection(
                    resource_requirements=resource_req,
                    selected_agent=selected_tracker.original_agent,
                )
            )

        # Apply the diff changes to the mutable agents list
        for tracker in state_trackers:
            agent = tracker.original_agent
            if tracker.additional_slots or tracker.additional_containers > 0:
                agent.occupied_slots = agent.occupied_slots + tracker.additional_slots
                agent.container_count = agent.container_count + tracker.additional_containers

        return selections

    async def _select_agent_tracker_for_requirements(
        self,
        state_trackers: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        designated_agent_ids: Optional[list[AgentId]] = None,
    ) -> AgentStateTracker:
        # First pass: filter by architecture (binary compatibility check)
        arch_compatible_trackers: list[AgentStateTracker] = []
        for tracker in state_trackers:
            agent = tracker.original_agent
            if agent.architecture == resource_req.required_architecture:
                arch_compatible_trackers.append(tracker)

        if not arch_compatible_trackers:
            # No agents with matching architecture
            available_archs = {t.original_agent.architecture for t in state_trackers}
            raise NoCompatibleAgentError(
                f"No agents with required architecture '{resource_req.required_architecture}'. "
                f"Available architectures: {', '.join(sorted(available_archs))}"
            )

        # Second pass: filter by resource availability (quantitative check)
        compatible_trackers: list[AgentStateTracker] = []
        error_messages: defaultdict[str, int] = defaultdict(int)
        agent_errors: dict[AgentId, str] = {}
        for tracker in arch_compatible_trackers:
            try:
                self._check_tracker_compatibility(
                    tracker,
                    resource_req,
                    config,
                )
                compatible_trackers.append(tracker)
            except Exception as e:
                error_messages[str(e)] += 1
                agent_errors[tracker.original_agent.agent_id] = str(e)

        if not compatible_trackers:
            error_messages_summary = "; ".join(
                f"{count}x {msg}" for msg, count in error_messages.items()
            )
            raise NoAvailableAgentError(f"no available agents. Details: {error_messages_summary}")

        # Handle designated agent if specified
        if designated_agent_ids:
            for tracker in compatible_trackers:
                if tracker.original_agent.agent_id in designated_agent_ids:
                    return tracker

            error_messages_list = []
            for designated_agent_id in designated_agent_ids:
                if designated_agent_id in agent_errors:
                    error_messages_list.append(
                        f"Designated agent '{designated_agent_id}' is not compatible. Details: {agent_errors[designated_agent_id]}"
                    )
            error_message = " ".join(error_messages) if error_messages else "not found"
            raise NoAvailableAgentError(
                f"Designated agent '{designated_agent_ids}' is not compatible. Details: {error_message}"
            )

        # Use strategy to select from compatible trackers
        return self._strategy.select_tracker_by_strategy(
            compatible_trackers, resource_req, criteria, config
        )

    def _check_tracker_compatibility(
        self,
        tracker: AgentStateTracker,
        resource_req: ResourceRequirements,
        config: AgentSelectionConfig,
    ) -> None:
        """Check if an agent tracker is compatible with the resource requirements.

        Note: Architecture compatibility is checked separately before this method.

        Raises:
            InsufficientResourcesError: If agent doesn't have enough resources
            ContainerLimitExceededError: If agent has reached container limit
        """
        agent = tracker.original_agent

        # Get current state with tracked changes
        occupied_slots = tracker.get_current_occupied_slots()
        container_count = tracker.get_current_container_count()

        # Check resource availability
        available_slots = agent.available_slots - occupied_slots
        if not (available_slots >= resource_req.requested_slots):
            # Build detailed message showing which resources are insufficient
            insufficient = []
            for k in resource_req.requested_slots.keys():
                requested_val = resource_req.requested_slots.get(k, 0)
                available_val = available_slots.get(k, 0)
                if requested_val > available_val:
                    insufficient.append(k)

            # Format values similar to group_resource_limit.py
            insufficient_details = {}
            for resource_name in insufficient:
                requested = resource_req.requested_slots.get(resource_name, 0)
                available = available_slots.get(resource_name, 0)

                # Format mem as human readable (e.g., "2 GiB" instead of raw bytes)
                if resource_name == "mem":
                    from ai.backend.common.types import BinarySize

                    insufficient_details[resource_name] = (
                        str(BinarySize(requested)),
                        str(BinarySize(available)),
                    )
                else:
                    # Store raw values for other resources
                    insufficient_details[resource_name] = (
                        str(requested),
                        str(available),
                    )

            raise InsufficientResourcesError(
                agent_id=agent.agent_id,
                requested_slots=resource_req.requested_slots,
                available_slots=available_slots,
                occupied_slots=occupied_slots,
                insufficient_resources=insufficient_details,
            )

        # Check container limit if specified
        if config.max_container_count is not None:
            if container_count >= config.max_container_count:
                raise ContainerLimitExceededError(
                    agent_id=agent.agent_id,
                    current_count=container_count,
                    max_count=config.max_container_count,
                )
