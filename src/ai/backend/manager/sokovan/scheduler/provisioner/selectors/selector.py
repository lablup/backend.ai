"""
Agent selector interface for sokovan scheduler.

This module defines the interface for agent selection that abstracts away
the row-based implementation details of the legacy selectors.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    AgentId,
    BinarySize,
    ClusterMode,
    KernelId,
    SessionId,
    SessionTypes,
    SlotName,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.data.sokovan import AgentInfo
from ai.backend.manager.data.sokovan.workload import ResourceRequest

from .exceptions import (
    BatchAgentSelectionFailedError,
    ContainerLimitExceededError,
    InsufficientResourcesError,
    NoAgentsInResourceGroupError,
    NoAvailableAgentError,
    NoCompatibleAgentError,
    RequirementSelectionError,
    TrackerCompatibilityError,
)
from .types import ResourceRequirements

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class AgentStateTracker:
    """Tracks in-batch allocations for one agent during a scheduling pass.

    The agent observation (``AgentInfo``) is immutable; every in-batch state
    change lives here. ``committed`` holds allocations from earlier sessions
    of this pass, ``pending`` holds the session currently being placed —
    the all-or-nothing per-session semantics come from commit()/rollback().
    """

    original_agent: AgentInfo
    committed_slots: dict[SlotName, Decimal] = field(default_factory=dict)
    committed_containers: int = 0
    pending_slots: dict[SlotName, Decimal] = field(default_factory=dict)
    pending_containers: int = 0

    def remaining_slots(self) -> dict[SlotName, Decimal]:
        """Per-slot remaining = capacity - reserved - used - in-batch allocations."""
        remaining: dict[SlotName, Decimal] = {}
        for slot_name, resource in self.original_agent.resources.slots.items():
            remaining[slot_name] = (
                resource.capacity
                - resource.reserved
                - resource.used
                - self.committed_slots.get(slot_name, Decimal(0))
                - self.pending_slots.get(slot_name, Decimal(0))
            )
        return remaining

    def current_container_count(self) -> int:
        """Get current container count including in-batch allocations."""
        return (
            self.original_agent.container_count
            + self.committed_containers
            + self.pending_containers
        )

    def apply_diff(self, request: ResourceRequest, containers: int) -> None:
        """Apply an in-flight allocation of the session being placed."""
        for slot_name, amount in request.slots.items():
            self.pending_slots[slot_name] = self.pending_slots.get(slot_name, Decimal(0)) + amount
        self.pending_containers += containers

    def commit(self) -> None:
        """Fold the in-flight allocation into the batch state (session placed)."""
        for slot_name, amount in self.pending_slots.items():
            self.committed_slots[slot_name] = (
                self.committed_slots.get(slot_name, Decimal(0)) + amount
            )
        self.committed_containers += self.pending_containers
        self.rollback()

    def rollback(self) -> None:
        """Discard the in-flight allocation (session placement failed)."""
        self.pending_slots = {}
        self.pending_containers = 0


@dataclass
class SessionMetadata:
    """Metadata for the session being scheduled."""

    # Session ID
    session_id: SessionId
    # Type of the session (e.g., INTERACTIVE, BATCH, INFERENCE)
    session_type: SessionTypes
    # Resource group the session belongs to
    resource_group_id: ResourceGroupID
    # Cluster mode (e.g., SINGLE, MULTI)
    cluster_mode: ClusterMode


@dataclass
class AgentSelectionConfig:
    """Configuration for agent selection."""

    # Maximum number of containers allowed per agent
    max_container_count: int | None
    # Whether to enforce endpoint replica spreading (from sgroup_opts)
    enforce_spreading_endpoint_replica: bool = False


@dataclass
class KernelResourceSpec:
    """Resource specification for a single kernel."""

    # Resource slots required
    requested_slots: ResourceRequest
    # Architecture required
    required_architecture: str


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
    kernel_requirements: Mapping[KernelId, KernelResourceSpec]
    # How designated agents are enforced (STRICT fails, PREFERRED falls back)
    agent_selection_policy: AgentSelectionPolicy
    # Kernel counts at endpoint for each agent (for concentrated selector spreading)
    kernel_counts_at_endpoint: Mapping[AgentId, int] | None = None
    # Agents that previously failed for this session (for deprioritization on retry)
    failed_agent_ids: frozenset[AgentId] = frozenset()
    # Manually designated agents (user's explicit choice takes precedence)
    designated_agent_ids: list[AgentId] | None = None

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
            total_slots: dict[SlotName, Decimal] = {}
            for kernel_req in self.kernel_requirements.values():
                for slot_name, amount in kernel_req.requested_slots.slots.items():
                    total_slots[slot_name] = total_slots.get(slot_name, Decimal(0)) + amount

            # Use the common architecture
            architecture = list(architectures)[0]
            # Include all kernel IDs in the aggregated requirement
            return [
                ResourceRequirements(
                    requested_slots=ResourceRequest(slots=total_slots),
                    required_architecture=architecture,
                    kernel_ids=list(self.kernel_requirements.keys()),
                )
            ]
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

    def strategy_name(self) -> str:
        """
        Return the strategy name for predicates.
        """
        return self._strategy.name()

    def strategy_success_message(self) -> str:
        """
        Return a message describing successful agent selection.
        """
        return self._strategy.success_message()

    async def select_agents_for_batch_requirements(
        self,
        trackers: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
    ) -> list[AgentSelection]:
        """
        Select agents for every resource requirement in the criteria.

        Every requirement is evaluated (a placement failure does not abort the
        batch early); if any requirement could not be placed, the whole batch
        fails and a :class:`BatchAgentSelectionFailedError` carrying every
        per-requirement failure (with its remediation hint) is raised. On full
        success the in-flight allocations are committed into the trackers so
        later sessions of the same scheduling pass observe them.

        Args:
            trackers: Batch-scoped agent state (created once per scheduling pass)
            criteria: Selection criteria including kernel requirements
            config: Configuration for agent selection

        Returns:
            The list of AgentSelection objects pairing requirements with agents.

        Raises:
            NoAgentsInResourceGroupError: If the resource group has no agents at all
            BatchAgentSelectionFailedError: If any requirement could not be placed
            ValueError: If architecture mismatch in single-node session
        """
        resource_requirements = criteria.get_resource_requirements()
        if not resource_requirements:
            # Empty list for sessions with no kernels
            return []
        if not trackers:
            raise NoAgentsInResourceGroupError(criteria.session_metadata.resource_group_id)

        selections: list[AgentSelection] = []
        errors: list[RequirementSelectionError] = []

        for resource_req in resource_requirements:
            # Capture a placement failure and continue evaluating the remaining
            # requirements so every failure's remediation hint is collected.
            try:
                selected_tracker = await self._select_agent_tracker_for_requirements(
                    trackers,
                    resource_req,
                    criteria,
                    config,
                )
            except (NoAvailableAgentError, NoCompatibleAgentError) as e:
                errors.append(e)
                continue

            # Track the in-flight allocation for the selected agent
            selected_tracker.apply_diff(resource_req.requested_slots, len(resource_req.kernel_ids))

            # Store the selection with the original agent
            selections.append(
                AgentSelection(
                    resource_requirements=resource_req,
                    selected_agent=selected_tracker.original_agent,
                )
            )

        if errors:
            # All-or-nothing per session: surface every requirement's failure.
            for tracker in trackers:
                tracker.rollback()
            raise BatchAgentSelectionFailedError(errors)

        # Full success: fold the session's allocations into the batch state
        for tracker in trackers:
            tracker.commit()

        return selections

    async def _select_agent_tracker_for_requirements(
        self,
        state_trackers: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
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
                resource_requirement=resource_req,
                available_architectures=sorted(available_archs),
            )

        # Second pass: filter by resource availability (quantitative check)
        compatible_trackers: list[AgentStateTracker] = []
        agent_errors: dict[AgentId, TrackerCompatibilityError] = {}
        for tracker in arch_compatible_trackers:
            try:
                self._check_tracker_compatibility(
                    tracker,
                    resource_req,
                    config,
                )
                compatible_trackers.append(tracker)
            except TrackerCompatibilityError as e:
                agent_errors[tracker.original_agent.agent_id] = e

        if not compatible_trackers:
            raise NoAvailableAgentError(
                resource_requirement=resource_req,
                agent_errors=agent_errors,
            )

        # Handle designated agents first (user's explicit choice takes precedence)
        if criteria.designated_agent_ids:
            for tracker in compatible_trackers:
                if tracker.original_agent.agent_id in criteria.designated_agent_ids:
                    return tracker

            if criteria.agent_selection_policy == AgentSelectionPolicy.STRICT:
                raise NoAvailableAgentError(
                    resource_requirement=resource_req,
                    agent_errors=agent_errors,
                    available_agent_ids=[
                        tracker.original_agent.agent_id for tracker in compatible_trackers
                    ],
                    designated_agent_ids=criteria.designated_agent_ids,
                )
            # PREFERRED: designated agents have no capacity - fall back to
            # the normal candidate path below

        # Third pass: deprioritize agents that previously failed for this session
        candidate_trackers = compatible_trackers
        if criteria.failed_agent_ids:
            non_failed = [
                tracker
                for tracker in compatible_trackers
                if tracker.original_agent.agent_id not in criteria.failed_agent_ids
            ]
            if non_failed:
                excluded = [
                    tracker.original_agent.agent_id
                    for tracker in compatible_trackers
                    if tracker.original_agent.agent_id in criteria.failed_agent_ids
                ]
                log.debug(
                    "failed-agent filter(session:{}): excluding {} → candidates: {}",
                    criteria.session_metadata.session_id,
                    excluded,
                    [tracker.original_agent.agent_id for tracker in non_failed],
                )
                candidate_trackers = non_failed
            else:
                log.debug(
                    "failed-agent filter(session:{}): all {} compatible agents have failed, "
                    "skipping filter to avoid blocking",
                    criteria.session_metadata.session_id,
                    len(compatible_trackers),
                )
            # If ALL compatible agents have failed, keep all of them to avoid blocking

        # Use strategy to select from candidates
        return self._strategy.select_tracker_by_strategy(
            candidate_trackers, resource_req, criteria, config
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
        remaining_slots = tracker.remaining_slots()
        container_count = tracker.current_container_count()

        # Check resource availability on the requested slots (missing = 0)
        insufficient_details: dict[SlotName, tuple[str, str]] = {}
        for slot_name, requested in resource_req.requested_slots.slots.items():
            available = remaining_slots.get(slot_name, Decimal(0))
            if requested > available:
                # Format mem as human readable (e.g., "2 GiB" instead of raw bytes)
                if slot_name == "mem":
                    insufficient_details[slot_name] = (
                        str(BinarySize(requested)),
                        str(BinarySize(available)),
                    )
                else:
                    # Store raw values for other resources
                    insufficient_details[slot_name] = (
                        str(requested),
                        str(available),
                    )

        if insufficient_details:
            raise InsufficientResourcesError(
                agent_id=agent.agent_id,
                requested_slots=resource_req.requested_slots.slots,
                available_slots=remaining_slots,
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
