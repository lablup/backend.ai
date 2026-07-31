"""Tests for the placement computation (``compute_placements``)."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId, AgentSelectionStrategy, PreemptionOrder, SessionId
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    NoCompatibleAgentError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.pool import (
    create_agent_selector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionCriteria,
    AgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.agent import (
    AgentInfo,
    AgentLimit,
    AgentResource,
    SlotResource,
)
from ai.backend.manager.views.sokovan.workload import ResourceRequest

NO_LIMIT = AgentLimit(max_container_count=None)


def _slots(slots: Mapping[str, str]) -> dict[ResourceSlotName, Decimal]:
    return {ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}


def _req(
    slots: Mapping[str, str],
    arch: str = "x86_64",
    containers: int = 1,
) -> ResourceRequirements:
    return ResourceRequirements(
        requested_slots=ResourceRequest(slots=_slots(slots)),
        required_architecture=ArchName(arch),
        container_count=containers,
    )


def _agent(
    agent_id: str,
    capacities: Mapping[str, str],
    container_count: int = 0,
) -> AgentInfo:
    return AgentInfo(
        agent_id=AgentId(agent_id),
        agent_addr=f"{agent_id}:6001",
        architecture=ArchName("x86_64"),
        resources=AgentResource(
            slots={
                ResourceSlotName(name): SlotResource(
                    capacity=Decimal(amount), reserved=Decimal(0), used=Decimal(0)
                )
                for name, amount in capacities.items()
            }
        ),
        container_count=container_count,
    )


def _criteria(requirements: list[ResourceRequirements]) -> AgentSelectionCriteria:
    return AgentSelectionCriteria(
        session_id=SessionId(uuid.uuid4()),
        resource_group_id=ResourceGroupID(uuid.UUID(int=0)),
        requirements=requirements,
        agent_selection_policy=AgentSelectionPolicy.STRICT,
        designated_agent_ids=None,
        job_priority=0,
        victim_candidates=None,
        session_group=None,
    )


def _trackers(agents: list[AgentInfo]) -> list[AgentStateTracker]:
    return [AgentStateTracker(original_agent=agent) for agent in agents]


def _selector() -> AgentSelector:
    return create_agent_selector(["cpu", "mem"])


class TestComputePlacements:
    """Resolvable placement failures are computed results, not exceptions."""

    async def test_unplaceable_requirement_is_a_result_not_an_error(self) -> None:
        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers([_agent("agent-a", {"cpu": "1"})]),
            _criteria([_req({"cpu": "4"})]),
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )
        assert computation.selections == []
        assert len(computation.failures) == 1

    async def test_all_requirements_are_evaluated(self) -> None:
        """A failed requirement does not stop evaluation of the rest."""
        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers([_agent("agent-a", {"cpu": "2"})]),
            _criteria([
                _req({"cpu": "8"}),  # impossible
                _req({"cpu": "1"}),  # placeable
            ]),
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )
        assert len(computation.failures) == 1
        assert computation.failures[0].requirement_index == 0
        assert len(computation.selections) == 1

    async def test_failure_rolls_back_tracker_state(self) -> None:
        """All-or-nothing: any failure leaves the batch state unchanged."""
        trackers = _trackers([_agent("agent-a", {"cpu": "2"})])
        await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            trackers,
            _criteria([_req({"cpu": "1"}), _req({"cpu": "8"})]),
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )
        for tracker in trackers:
            assert tracker.pending_slots == {}
            assert tracker.committed_slots == {}

    async def test_absolute_failure_rolls_back_tracker_state(self) -> None:
        """A propagated exclusion failure also keeps all-or-nothing."""
        trackers = _trackers([_agent("agent-a", {"cpu": "2"})])
        with pytest.raises(NoCompatibleAgentError):
            await _selector().compute_placements(
                AgentSelectionStrategy.CONCENTRATED,
                trackers,
                _criteria([_req({"cpu": "1"}), _req({"cpu": "1"}, arch="aarch64")]),
                NO_LIMIT,
                PreemptionOrder.OLDEST,
            )
        for tracker in trackers:
            assert tracker.pending_slots == {}
            assert tracker.committed_slots == {}


class TestMissingSlots:
    """The shortfall is measured against the best-fitting candidate."""

    async def test_shortfall_uses_smallest_total_shortage(self) -> None:
        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers([
                _agent("agent-small", {"cpu": "1"}),  # short by 3
                _agent("agent-close", {"cpu": "3"}),  # short by 1
            ]),
            _criteria([_req({"cpu": "4"})]),
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )
        failure = computation.failures[0]
        assert failure.missing_slots == _slots({"cpu": "1"})
        assert failure.missing_containers == 0

    async def test_shortfall_keeps_only_short_slots(self) -> None:
        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers([_agent("agent-a", {"cpu": "1", "mem": "10000"})]),
            _criteria([_req({"cpu": "4", "mem": "8192"})]),  # mem is sufficient
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )
        assert computation.failures[0].missing_slots == _slots({"cpu": "3"})

    async def test_exclusion_failure_propagates_as_error(self) -> None:
        """An exclusion filter emptying the pool is an absolute failure,
        not a computed result."""
        with pytest.raises(NoCompatibleAgentError) as exc_info:
            await _selector().compute_placements(
                AgentSelectionStrategy.CONCENTRATED,
                _trackers([_agent("agent-a", {"cpu": "8"})]),
                _criteria([_req({"cpu": "1"}, arch="aarch64")]),
                NO_LIMIT,
                PreemptionOrder.OLDEST,
            )
        assert exc_info.value.filter_name == "architecture"

    async def test_container_limit_failure_has_empty_shortfall(self) -> None:
        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers([_agent("agent-a", {"cpu": "8"}, container_count=10)]),
            _criteria([_req({"cpu": "1"})]),
            AgentLimit(max_container_count=10),
            PreemptionOrder.OLDEST,
        )
        failure = computation.failures[0]
        assert failure.filter_name == "container-limit"
        assert failure.missing_slots == {}
        assert failure.missing_containers == 1
