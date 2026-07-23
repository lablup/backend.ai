"""
Agent selector interface for sokovan scheduler.

This module defines the interface for agent selection that abstracts away
the row-based implementation details of the legacy selectors.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    AgentId,
    BinarySize,
    ClusterMode,
    SessionId,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.views.sokovan.agent import AgentInfo, AgentLimit
from ai.backend.manager.views.sokovan.workload import (
    ResourceRequest,
    SessionPlacement,
    SessionWorkload,
)

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
from .tracker import AgentStateTracker
from .types import ResourceRequirements

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class AgentSelection:
    """Result of selecting an agent for specific resource requirements."""

    resource_requirements: ResourceRequirements
    selected_agent: AgentInfo


@dataclass
class AgentSelectionCriteria:
    """What one placement request asks of the agent pool.

    Holds only what the selection itself consumes: the placement
    requirements plus the session-scoped hints (retry filter, designated
    agents). Kernel bookkeeping stays with the caller, which maps the
    order-aligned selections (or ``requirement_index`` on failures) back
    to its own kernel groups.
    """

    # Session the placement is for (failed-agent retry filter)
    session_id: SessionId
    # Resource group the candidates were drawn from (error context)
    resource_group_id: ResourceGroupID
    # Placement requirements, already grouped by cluster mode
    requirements: Sequence[ResourceRequirements]
    # How designated agents are enforced (STRICT fails, PREFERRED falls back)
    agent_selection_policy: AgentSelectionPolicy
    # Manually designated agents (user's explicit choice takes precedence)
    designated_agent_ids: list[AgentId] | None

    @classmethod
    def from_workload(
        cls,
        workload: SessionWorkload,
        plan: PlacementPlan,
    ) -> AgentSelectionCriteria:
        """Project a session workload (and its grouped plan) into criteria."""
        return cls(
            session_id=workload.meta.session_id,
            resource_group_id=workload.meta.resource_group_id,
            requirements=plan.requirements(),
            agent_selection_policy=workload.placement.agent_selection_policy,
            designated_agent_ids=workload.placement.designated_agent_ids,
        )


@dataclass
class PlacementGroup:
    """One placement requirement paired with the positions of the input
    items it was built from.

    The plan itself is kernel-agnostic; each caller resolves the indices
    back to its own domain (kernel rows for the scheduling pass, request
    entries for the fitting check).
    """

    requirement: ResourceRequirements
    indices: list[int]


@dataclass
class PlacementPlan:
    """The session's placement groups, order-aligned with the selections
    (and with ``requirement_index`` on failures)."""

    groups: list[PlacementGroup]

    @classmethod
    def from_items(
        cls,
        items: Sequence[ResourceRequirements],
        cluster_mode: ClusterMode,
    ) -> PlacementPlan:
        """Group per-item requirements into placement groups by cluster mode.

        Single-node sessions merge every item into one requirement (one
        agent hosts all containers, slots summed, architectures must
        agree); multi-node sessions keep one group per item.

        Raises:
            ValueError: If a single-node session mixes architectures.
        """
        if not items:
            return cls(groups=[])

        if cluster_mode == ClusterMode.SINGLE_NODE:
            architectures = {item.required_architecture for item in items}
            if len(architectures) > 1:
                raise ValueError(
                    f"Single-node session has kernels with different architectures: {architectures}"
                )

            total_slots: dict[ResourceSlotName, Decimal] = {}
            for item in items:
                for slot_name, amount in item.requested_slots.slots.items():
                    total_slots[slot_name] = total_slots.get(slot_name, Decimal(0)) + amount

            group = PlacementGroup(
                requirement=ResourceRequirements(
                    requested_slots=ResourceRequest(slots=total_slots),
                    required_architecture=architectures.pop(),
                    container_count=sum(item.container_count for item in items),
                ),
                indices=list(range(len(items))),
            )
            return cls(groups=[group])

        return cls(
            groups=[
                PlacementGroup(requirement=item, indices=[index])
                for index, item in enumerate(items)
            ]
        )

    @classmethod
    def from_placement(cls, placement: SessionPlacement) -> PlacementPlan:
        """Project a session placement into the plan; indices refer to
        positions in ``placement.kernels``."""
        return cls.from_items(
            [
                ResourceRequirements(
                    requested_slots=kernel.requested_slots,
                    required_architecture=kernel.architecture,
                    container_count=1,
                )
                for kernel in placement.kernels
            ],
            placement.cluster_mode,
        )

    def requirements(self) -> list[ResourceRequirements]:
        return [group.requirement for group in self.groups]


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
    ) -> AgentStateTracker:
        """
        Select an agent tracker using the strategy with specific resource requirements.

        This method should implement the core selection logic without
        handling designated agents or common filtering.

        Args:
            trackers: Pre-filtered compatible trackers (guaranteed non-empty)
            resource_req: Resource requirements to satisfy

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
        limit: AgentLimit,
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
            limit: Per-agent cap enforced during selection

        Returns:
            The list of AgentSelection objects pairing requirements with agents.

        Raises:
            NoAgentsInResourceGroupError: If the resource group has no agents at all
            BatchAgentSelectionFailedError: If any requirement could not be placed
            ValueError: If architecture mismatch in single-node session
        """
        if not criteria.requirements:
            # Empty list for sessions with no kernels
            return []
        if not trackers:
            raise NoAgentsInResourceGroupError(criteria.resource_group_id)

        selections: list[AgentSelection] = []
        errors: list[RequirementSelectionError] = []

        for requirement_index, resource_req in enumerate(criteria.requirements):
            # Capture a placement failure and continue evaluating the remaining
            # requirements so every failure's remediation hint is collected.
            try:
                selected_tracker = await self._select_agent_tracker_for_requirements(
                    trackers,
                    resource_req,
                    requirement_index,
                    criteria,
                    limit,
                )
            except (NoAvailableAgentError, NoCompatibleAgentError) as e:
                errors.append(e)
                continue

            # Track the in-flight allocation for the selected agent
            selected_tracker.apply_diff(resource_req.requested_slots, resource_req.container_count)

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
        requirement_index: int,
        criteria: AgentSelectionCriteria,
        limit: AgentLimit,
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
                requirement_index=requirement_index,
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
                    limit,
                )
                compatible_trackers.append(tracker)
            except TrackerCompatibilityError as e:
                agent_errors[tracker.original_agent.agent_id] = e

        if not compatible_trackers:
            raise NoAvailableAgentError(
                resource_requirement=resource_req,
                requirement_index=requirement_index,
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
                    requirement_index=requirement_index,
                    agent_errors=agent_errors,
                    available_agent_ids=[
                        tracker.original_agent.agent_id for tracker in compatible_trackers
                    ],
                    designated_agent_ids=criteria.designated_agent_ids,
                )
            # PREFERRED: designated agents have no capacity - fall back to
            # the normal candidate path below

        # Third pass: deprioritize agents where this session previously failed
        session_id = criteria.session_id
        candidate_trackers = compatible_trackers
        non_failed = [
            tracker
            for tracker in compatible_trackers
            if session_id not in tracker.failed_session_ids
        ]
        if len(non_failed) < len(compatible_trackers):
            if non_failed:
                excluded = [
                    tracker.original_agent.agent_id
                    for tracker in compatible_trackers
                    if session_id in tracker.failed_session_ids
                ]
                log.debug(
                    "failed-agent filter(session:{}): excluding {} → candidates: {}",
                    session_id,
                    excluded,
                    [tracker.original_agent.agent_id for tracker in non_failed],
                )
                candidate_trackers = non_failed
            else:
                # If ALL compatible agents have failed, keep all of them to avoid blocking
                log.debug(
                    "failed-agent filter(session:{}): all {} compatible agents have failed, "
                    "skipping filter to avoid blocking",
                    session_id,
                    len(compatible_trackers),
                )

        # Use strategy to select from candidates
        return self._strategy.select_tracker_by_strategy(candidate_trackers, resource_req)

    def _check_tracker_compatibility(
        self,
        tracker: AgentStateTracker,
        resource_req: ResourceRequirements,
        limit: AgentLimit,
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
        insufficient_details: dict[ResourceSlotName, tuple[str, str]] = {}
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
        if limit.max_container_count is not None:
            if container_count >= limit.max_container_count:
                raise ContainerLimitExceededError(
                    agent_id=agent.agent_id,
                    current_count=container_count,
                    max_count=limit.max_container_count,
                )
