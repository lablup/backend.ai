"""
Agent selector interface for sokovan scheduler.

This module defines the interface for agent selection that abstracts away
the row-based implementation details of the legacy selectors.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    AgentId,
    AgentSelectionStrategy,
    ClusterMode,
    PreemptionOrder,
    SessionId,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.recorder.recorder import TransitionRecorder
from ai.backend.manager.views.sokovan.agent import AgentInfo, AgentLimit
from ai.backend.manager.views.sokovan.snapshot import PreemptionCandidate, UserVictimCandidates
from ai.backend.manager.views.sokovan.workload import (
    ResourceRequest,
    SessionPlacement,
    SessionWorkload,
)

from .exceptions import (
    BatchAgentSelectionFailedError,
    NoAgentsInResourceGroupError,
    NoAvailableAgentError,
    NoCompatibleAgentError,
)
from .filters.exclusion.filter import AbstractExclusionTrackerFilter
from .filters.stateful.filter import AbstractStatefulTrackerFilter
from .orders.order import AbstractTrackerOrder
from .tracker import AgentStateTracker
from .types import PlacementFailure, ResourceRequirements
from .victims.selector import VictimSelector

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class AgentSelection:
    """Result of selecting an agent for specific resource requirements."""

    resource_requirements: ResourceRequirements
    selected_agent: AgentInfo
    # Sessions that must be preempted for this placement to fit (empty for
    # a normal placement; a non-empty tuple marks a preemption proposal)
    preempting_session_ids: tuple[SessionId, ...]


@dataclass
class PlacementComputation:
    """The whole batch's computed placements: successes and the
    requirements that cannot be placed. Never expressed as an exception."""

    selections: list[AgentSelection]
    failures: list[PlacementFailure]


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
    # Scope-local preemption priority: only strictly lower victims may be
    # reclaimed for this session (the neutral 0 reclaims nothing)
    job_priority: int
    # The owner's preemption victim candidates (None disables the
    # preemption path, e.g. the fitting check)
    victim_candidates: UserVictimCandidates | None

    @classmethod
    def from_workload(
        cls,
        workload: SessionWorkload,
        plan: PlacementPlan,
        victim_candidates: UserVictimCandidates | None,
    ) -> AgentSelectionCriteria:
        """Project a session workload (and its grouped plan) into criteria."""
        return cls(
            session_id=workload.meta.session_id,
            resource_group_id=workload.meta.resource_group_id,
            requirements=plan.requirements(),
            agent_selection_policy=workload.placement.agent_selection_policy,
            designated_agent_ids=workload.placement.designated_agent_ids,
            job_priority=workload.job_priority,
            victim_candidates=victim_candidates,
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
    Agent selection pipeline: filters -> orders -> strategy pick.

    Exclusion filters drop agents no state change can save, stateful
    filters drop agents whose current resources fall short, orders narrow
    the survivors to the preferred tier, and the pooled strategy picks one.
    A single instance (built once via ``pool.create_agent_selector``)
    serves every resource group.
    """

    _strategy_pool: Mapping[AgentSelectionStrategy, AbstractAgentSelector]
    _exclusion_filters: Sequence[AbstractExclusionTrackerFilter]
    _stateful_filters: Sequence[AbstractStatefulTrackerFilter]
    _orders: Sequence[AbstractTrackerOrder]
    _victim_selector: VictimSelector

    def __init__(
        self,
        strategy_pool: Mapping[AgentSelectionStrategy, AbstractAgentSelector],
        exclusion_filters: Sequence[AbstractExclusionTrackerFilter],
        stateful_filters: Sequence[AbstractStatefulTrackerFilter],
        orders: Sequence[AbstractTrackerOrder],
        victim_selector: VictimSelector,
    ) -> None:
        self._strategy_pool = strategy_pool
        self._exclusion_filters = exclusion_filters
        self._stateful_filters = stateful_filters
        self._orders = orders
        self._victim_selector = victim_selector

    def strategy_name(self, strategy: AgentSelectionStrategy) -> str:
        """
        Return the strategy name for predicates.
        """
        return self._strategy_pool[strategy].name()

    def strategy_success_message(self, strategy: AgentSelectionStrategy) -> str:
        """
        Return a message describing successful agent selection.
        """
        return self._strategy_pool[strategy].success_message()

    async def compute_placements(
        self,
        strategy: AgentSelectionStrategy,
        trackers: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        limit: AgentLimit,
        preemption_order: PreemptionOrder,
    ) -> PlacementComputation:
        """Compute placements for every resource requirement in the criteria.

        The computation core: resolvable placement failures are results, not
        exceptions. Each requirement runs the exclusion chain, the stateful
        chain, the order tiers, and the pooled strategy pick; when a stateful
        filter leaves no candidates the requirement is recorded as a
        :class:`PlacementFailure` (with the per-slot shortfall) and the
        remaining requirements are still evaluated.

        All-or-nothing batch semantics: with any failure the in-flight
        allocations are rolled back. On full success without preemption they
        are committed so later sessions of the same scheduling pass observe
        them; a session with any preemption is a proposal, so its state
        (diffs and victim reclaims, kept only while its own requirements are
        being placed) is rolled back too — the plan lives in the selections,
        never in the trackers.

        Raises:
            NoAgentsInResourceGroupError: If the resource group has no agents
                at all (a precondition, not a placement outcome)
            NoCompatibleAgentError: If an exclusion filter leaves no
                candidates (absolute failure — no state change can fix it)
        """
        if not criteria.requirements:
            # Empty computation for sessions with no kernels
            return PlacementComputation(selections=[], failures=[])
        if not trackers:
            raise NoAgentsInResourceGroupError(criteria.resource_group_id)

        recorder = self._current_recorder(criteria.session_id)
        computation = PlacementComputation(selections=[], failures=[])
        claimed_victims: list[PreemptionCandidate] = []

        try:
            for requirement_index, resource_req in enumerate(criteria.requirements):
                try:
                    selection = self._place_requirement(
                        strategy,
                        trackers,
                        criteria,
                        resource_req,
                        limit,
                        preemption_order,
                        claimed_victims,
                        recorder,
                    )
                except NoAvailableAgentError as e:
                    computation.failures.append(
                        PlacementFailure(
                            requirement_index=requirement_index,
                            resource_requirement=resource_req,
                            filter_name=e.filter_name,
                            missing_slots=e.missing_slots,
                            missing_containers=e.missing_containers,
                        )
                    )
                    continue
                computation.selections.append(selection)
        except Exception:
            # Any propagating error (absolute failures included) aborts the
            # batch; roll back so the shared trackers stay all-or-nothing.
            self._discard_session_state(trackers)
            raise

        if computation.failures:
            self._discard_session_state(trackers)
        else:
            # A session with preemption reserves its resources for real, so
            # its diffs commit like any placement; only the victims' credit
            # (not actual resources yet) is dropped.
            for tracker in trackers:
                tracker.commit()
                tracker.clear_reclaim()

        return computation

    def _discard_session_state(self, trackers: Sequence[AgentStateTracker]) -> None:
        """Drop the session's in-flight diffs and victim reclaims."""
        for tracker in trackers:
            tracker.rollback()
            tracker.clear_reclaim()

    def _place_requirement(
        self,
        strategy: AgentSelectionStrategy,
        trackers: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
        limit: AgentLimit,
        preemption_order: PreemptionOrder,
        claimed_victims: list[PreemptionCandidate],
        recorder: TransitionRecorder[SessionId] | None,
    ) -> AgentSelection:
        """Place one requirement: filter chains, order tiers, strategy pick.
        When the stateful chain empties, retry with the owner's preemption
        victims reclaimed before giving up.

        Raises:
            NoCompatibleAgentError: When an exclusion filter leaves no
                candidates (absolute failure)
            NoAvailableAgentError: When a stateful filter leaves no
                candidates and preemption cannot help either
        """
        candidates = self._run_exclusion_filters(trackers, criteria, resource_req, recorder)
        try:
            candidates = self._run_stateful_filters(
                candidates, criteria, resource_req, limit, recorder
            )
        except NoAvailableAgentError:
            victims = self._reclaimable_victims(criteria, claimed_victims)
            if victims is None:
                raise
            return self._place_with_preemption(
                strategy,
                trackers,
                candidates,
                victims,
                criteria,
                resource_req,
                limit,
                preemption_order,
                claimed_victims,
                recorder,
            )

        candidates = self._narrow_by_orders(candidates, criteria)
        selected_tracker = self._strategy_pool[strategy].select_tracker_by_strategy(
            candidates, resource_req
        )
        # Track the in-flight allocation for the selected agent
        selected_tracker.apply_diff(resource_req.requested_slots, resource_req.container_count)
        return AgentSelection(
            resource_requirements=resource_req,
            selected_agent=selected_tracker.original_agent,
            preempting_session_ids=(),
        )

    def _place_with_preemption(
        self,
        strategy: AgentSelectionStrategy,
        trackers: Sequence[AgentStateTracker],
        candidates: Sequence[AgentStateTracker],
        victims: UserVictimCandidates,
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
        limit: AgentLimit,
        preemption_order: PreemptionOrder,
        claimed_victims: list[PreemptionCandidate],
        recorder: TransitionRecorder[SessionId] | None,
    ) -> AgentSelection:
        """Retry the stateful chain with the owner's unclaimed victims
        provisionally reclaimed; on success propose (not execute) the
        preemption.

        ``candidates`` are the exclusion survivors of this requirement and
        ``victims`` the unclaimed reclaimable set. The chosen victims join
        ``claimed_victims``: their allocations stay reclaimed on every agent
        they touch (a victim dies once, freeing everywhere) and the
        requirement's allocation is applied, so the session's remaining
        requirements compute against the proposed state. The whole session
        state is discarded after the batch — proposals never leak into the
        trackers other sessions see.

        Raises:
            NoAvailableAgentError: When preemption cannot make any agent fit.
        """
        victims_by_agent = victims.by_agent
        shortfalls = {
            tracker.original_agent.agent_id: self._shortfall(tracker, resource_req)
            for tracker in candidates
        }
        # Probe: credit every unclaimed victim in full, on top of the state
        # already carrying the session's previous claims and allocations.
        for tracker in candidates:
            agent_victims = victims_by_agent.get(tracker.original_agent.agent_id)
            if agent_victims is not None:
                tracker.apply_reclaim(agent_victims.total_reclaimable)
        try:
            feasible = self._run_stateful_filters(
                candidates, criteria, resource_req, limit, recorder
            )
            feasible = self._narrow_by_orders(feasible, criteria)
            feasible = self._victim_selector.narrow_agents(
                preemption_order, feasible, victims_by_agent, shortfalls
            )
            selected_tracker = self._strategy_pool[strategy].select_tracker_by_strategy(
                feasible, resource_req
            )
            selected_agent_id = selected_tracker.original_agent.agent_id
            chosen = self._victim_selector.collect_victims(
                preemption_order,
                victims_by_agent[selected_agent_id],
                shortfalls[selected_agent_id],
            )
        finally:
            # Drop the probe surplus: back to exactly the claims made so far.
            self._reset_reclaims(trackers, claimed_victims)
        claimed_victims.extend(chosen)
        # The new claims reclaim on every agent they touch (a victim dies
        # once, freeing everywhere); the requirement consumes from the
        # chosen agent.
        self._apply_victim_reclaims(trackers, chosen)
        selected_tracker.apply_diff(resource_req.requested_slots, resource_req.container_count)
        return AgentSelection(
            resource_requirements=resource_req,
            selected_agent=selected_tracker.original_agent,
            preempting_session_ids=tuple(candidate.session_id for candidate in chosen),
        )

    def _reclaimable_victims(
        self,
        criteria: AgentSelectionCriteria,
        claimed_victims: Sequence[PreemptionCandidate],
    ) -> UserVictimCandidates | None:
        """The owner's victims this session may still reclaim (strictly
        lower job_priority, not already claimed), or None when the
        preemption path does not apply."""
        if criteria.victim_candidates is None:
            return None
        claimed_ids = {candidate.session_id for candidate in claimed_victims}
        reclaimable = [
            candidate
            for candidate in criteria.victim_candidates.candidates
            if candidate.job_priority < criteria.job_priority
            and candidate.session_id not in claimed_ids
        ]
        if not reclaimable:
            return None
        return UserVictimCandidates(candidates=reclaimable)

    def _reset_reclaims(
        self,
        trackers: Sequence[AgentStateTracker],
        claimed_victims: Sequence[PreemptionCandidate],
    ) -> None:
        """Rebuild every tracker's reclaim to exactly the claimed victims'
        allocations (dropping any probe surplus)."""
        for tracker in trackers:
            tracker.clear_reclaim()
        self._apply_victim_reclaims(trackers, claimed_victims)

    def _apply_victim_reclaims(
        self,
        trackers: Sequence[AgentStateTracker],
        victims: Sequence[PreemptionCandidate],
    ) -> None:
        """Reclaim the victims' allocations on every agent they touch."""
        for tracker in trackers:
            agent_id = tracker.original_agent.agent_id
            for candidate in victims:
                portion = candidate.allocated_slots_by_agent.get(agent_id)
                if portion:
                    tracker.apply_reclaim(portion)

    def _shortfall(
        self,
        tracker: AgentStateTracker,
        resource_req: ResourceRequirements,
    ) -> Mapping[ResourceSlotName, Decimal]:
        """Per-slot shortage of one agent against the requirement."""
        remaining = tracker.remaining_slots()
        return {
            slot_name: shortage
            for slot_name, requested in resource_req.requested_slots.slots.items()
            if (shortage := requested - remaining.get(slot_name, Decimal(0))) > Decimal(0)
        }

    def _narrow_by_orders(
        self,
        candidates: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
    ) -> Sequence[AgentStateTracker]:
        for order in self._orders:
            best = min(order.rank(tracker, criteria) for tracker in candidates)
            candidates = [
                tracker for tracker in candidates if order.rank(tracker, criteria) == best
            ]
        return candidates

    def _run_exclusion_filters(
        self,
        candidates: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
        recorder: TransitionRecorder[SessionId] | None,
    ) -> Sequence[AgentStateTracker]:
        for exclusion in self._exclusion_filters:
            step = (
                recorder.step(exclusion.name(), success_detail=exclusion.success_message())
                if recorder is not None
                else nullcontext()
            )
            with step:
                candidates = exclusion.filter(candidates, criteria, resource_req)
                if not candidates:
                    # Raised inside the step so the record names the filter.
                    raise NoCompatibleAgentError(exclusion.name())
        return candidates

    def _run_stateful_filters(
        self,
        candidates: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
        limit: AgentLimit,
        recorder: TransitionRecorder[SessionId] | None,
    ) -> Sequence[AgentStateTracker]:
        entrants = candidates
        for stateful in self._stateful_filters:
            step = (
                recorder.step(stateful.name(), success_detail=stateful.success_message())
                if recorder is not None
                else nullcontext()
            )
            with step:
                candidates = stateful.filter(candidates, criteria, resource_req, limit)
                if not candidates:
                    # Raised inside the step so the record names the filter.
                    raise NoAvailableAgentError(
                        stateful.name(),
                        self._missing_slots(entrants, resource_req),
                        self._missing_containers(entrants, limit),
                    )
        return candidates

    async def select_agents_for_batch_requirements(
        self,
        strategy: AgentSelectionStrategy,
        trackers: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        limit: AgentLimit,
        preemption_order: PreemptionOrder,
    ) -> list[AgentSelection]:
        """The exception wrapper over :meth:`compute_placements` for the
        scheduling path: any computed failure fails the whole batch. This is
        the single place a placement failure becomes an error.

        Raises:
            NoAgentsInResourceGroupError: If the resource group has no agents at all
            BatchAgentSelectionFailedError: If any requirement could not be placed
        """
        computation = await self.compute_placements(
            strategy, trackers, criteria, limit, preemption_order
        )
        if computation.failures:
            raise BatchAgentSelectionFailedError(computation.failures)
        return computation.selections

    def _current_recorder(self, session_id: SessionId) -> TransitionRecorder[SessionId] | None:
        """The active recorder, or None outside a recording scope (the
        compute-schedule fitting check records nothing)."""
        try:
            pool = RecorderContext[SessionId].current_pool()
        except LookupError:
            return None
        return pool.recorder(session_id)

    def _missing_slots(
        self,
        candidates: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
    ) -> Mapping[ResourceSlotName, Decimal]:
        """Per-slot shortfall against the best-fitting candidate (the one
        with the smallest total shortage). Empty when no slot is short
        (e.g. the pool was emptied by the container limit)."""
        best: dict[ResourceSlotName, Decimal] = {}
        best_total: Decimal | None = None
        for tracker in candidates:
            remaining = tracker.remaining_slots()
            shortfall = {
                slot_name: shortage
                for slot_name, requested in resource_req.requested_slots.slots.items()
                if (shortage := requested - remaining.get(slot_name, Decimal(0))) > Decimal(0)
            }
            total = sum(shortfall.values(), Decimal(0))
            if best_total is None or total < best_total:
                best = shortfall
                best_total = total
        return best

    def _missing_containers(
        self,
        candidates: Sequence[AgentStateTracker],
        limit: AgentLimit,
    ) -> int:
        """How many containers the best candidate must free to admit one
        more (0 when some candidate is below the limit, or no limit)."""
        if limit.max_container_count is None:
            return 0
        return min(
            max(0, tracker.current_container_count() - limit.max_container_count + 1)
            for tracker in candidates
        )
