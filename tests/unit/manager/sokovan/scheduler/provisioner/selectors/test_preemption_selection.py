"""Tests for the preemption path of agent selection (stateful-failure retry)."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    AgentId,
    AgentSelectionStrategy,
    PreemptionOrder,
    SessionId,
)
from ai.backend.manager.data.session.options import AgentSelectionPolicy
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
from ai.backend.manager.views.sokovan.snapshot import (
    PreemptionCandidate,
    UserVictimCandidates,
)
from ai.backend.manager.views.sokovan.workload import ResourceRequest

NO_LIMIT = AgentLimit(max_container_count=None)


def _slots(slots: Mapping[str, str]) -> dict[ResourceSlotName, Decimal]:
    return {ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}


def _req(slots: Mapping[str, str]) -> ResourceRequirements:
    return ResourceRequirements(
        requested_slots=ResourceRequest(slots=_slots(slots)),
        required_architecture=ArchName("x86_64"),
        container_count=1,
    )


def _agent(agent_id: str, capacities: Mapping[str, str], used: Mapping[str, str]) -> AgentInfo:
    return AgentInfo(
        agent_id=AgentId(agent_id),
        agent_addr=f"{agent_id}:6001",
        architecture=ArchName("x86_64"),
        resources=AgentResource(
            slots={
                ResourceSlotName(name): SlotResource(
                    capacity=Decimal(amount),
                    reserved=Decimal(0),
                    used=Decimal(used.get(name, "0")),
                )
                for name, amount in capacities.items()
            }
        ),
        container_count=0,
    )


def _victim(
    session_id: SessionId,
    job_priority: int,
    started_year: int | None,
    slots_by_agent: Mapping[str, Mapping[str, str]],
) -> PreemptionCandidate:
    return PreemptionCandidate(
        session_id=session_id,
        job_priority=job_priority,
        started_at=(datetime(started_year, 1, 1, tzinfo=UTC) if started_year is not None else None),
        allocated_slots_by_agent={
            AgentId(agent_id): _slots(slots) for agent_id, slots in slots_by_agent.items()
        },
    )


def _criteria(
    requirements: list[ResourceRequirements],
    *,
    job_priority: int,
    victim_candidates: UserVictimCandidates | None,
) -> AgentSelectionCriteria:
    return AgentSelectionCriteria(
        session_id=SessionId(uuid.uuid4()),
        resource_group_id=ResourceGroupID(uuid.UUID(int=0)),
        requirements=requirements,
        agent_selection_policy=AgentSelectionPolicy.STRICT,
        designated_agent_ids=None,
        job_priority=job_priority,
        victim_candidates=victim_candidates,
    )


def _trackers(agents: list[AgentInfo]) -> list[AgentStateTracker]:
    return [AgentStateTracker(original_agent=agent) for agent in agents]


def _selector() -> AgentSelector:
    return create_agent_selector(["cpu", "mem"])


OLD_SESSION = SessionId(uuid.UUID(int=1))
NEW_SESSION = SessionId(uuid.UUID(int=2))
HIGH_PRIORITY_SESSION = SessionId(uuid.UUID(int=3))


class TestPreemptionPath:
    """A stateful failure retries with the owner's lower-priority victims."""

    @pytest.fixture
    def full_agent(self) -> list[AgentInfo]:
        # capacity 8, used 8 -> nothing remains without preemption
        return [_agent("agent-a", {"cpu": "8"}, used={"cpu": "8"})]

    async def test_lower_priority_victims_admit_the_session(
        self,
        full_agent: list[AgentInfo],
    ) -> None:
        victims = UserVictimCandidates(
            candidates=[
                _victim(OLD_SESSION, 1, 2020, {"agent-a": {"cpu": "2"}}),
                _victim(NEW_SESSION, 1, 2024, {"agent-a": {"cpu": "2"}}),
            ]
        )
        criteria = _criteria([_req({"cpu": "2"})], job_priority=5, victim_candidates=victims)
        trackers = _trackers(full_agent)

        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            trackers,
            criteria,
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )

        assert len(computation.selections) == 1
        selection = computation.selections[0]
        assert selection.selected_agent.agent_id == AgentId("agent-a")
        # cpu=2 shortfall is covered by one victim; OLDEST takes the older
        assert selection.preempting_session_ids == (OLD_SESSION,)

    async def test_newest_order_takes_the_younger_victim(
        self,
        full_agent: list[AgentInfo],
    ) -> None:
        victims = UserVictimCandidates(
            candidates=[
                _victim(OLD_SESSION, 1, 2020, {"agent-a": {"cpu": "2"}}),
                _victim(NEW_SESSION, 1, 2024, {"agent-a": {"cpu": "2"}}),
            ]
        )
        criteria = _criteria([_req({"cpu": "2"})], job_priority=5, victim_candidates=victims)

        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers(full_agent),
            criteria,
            NO_LIMIT,
            PreemptionOrder.NEWEST,
        )

        assert computation.selections[0].preempting_session_ids == (NEW_SESSION,)

    async def test_lower_job_priority_victims_come_first(
        self,
        full_agent: list[AgentInfo],
    ) -> None:
        """job_priority ascending precedes the order key."""
        victims = UserVictimCandidates(
            candidates=[
                _victim(OLD_SESSION, 3, 2020, {"agent-a": {"cpu": "2"}}),
                _victim(NEW_SESSION, 1, 2024, {"agent-a": {"cpu": "2"}}),
            ]
        )
        criteria = _criteria([_req({"cpu": "2"})], job_priority=5, victim_candidates=victims)

        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers(full_agent),
            criteria,
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )

        assert computation.selections[0].preempting_session_ids == (NEW_SESSION,)

    async def test_equal_or_higher_priority_victims_do_not_help(
        self,
        full_agent: list[AgentInfo],
    ) -> None:
        """Only strictly lower job_priority sessions may be reclaimed."""
        victims = UserVictimCandidates(
            candidates=[
                _victim(HIGH_PRIORITY_SESSION, 5, 2020, {"agent-a": {"cpu": "8"}}),
            ]
        )
        criteria = _criteria([_req({"cpu": "2"})], job_priority=5, victim_candidates=victims)

        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers(full_agent),
            criteria,
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )

        assert computation.selections == []
        assert computation.failures[0].filter_name == "resource"

    async def test_insufficient_victims_keep_the_failure(
        self,
        full_agent: list[AgentInfo],
    ) -> None:
        victims = UserVictimCandidates(
            candidates=[
                _victim(OLD_SESSION, 1, 2020, {"agent-a": {"cpu": "1"}}),
            ]
        )
        criteria = _criteria([_req({"cpu": "4"})], job_priority=5, victim_candidates=victims)

        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers(full_agent),
            criteria,
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )

        assert computation.selections == []
        assert len(computation.failures) == 1

    async def test_accumulates_victims_until_covered(
        self,
        full_agent: list[AgentInfo],
    ) -> None:
        victims = UserVictimCandidates(
            candidates=[
                _victim(OLD_SESSION, 1, 2020, {"agent-a": {"cpu": "2"}}),
                _victim(NEW_SESSION, 1, 2024, {"agent-a": {"cpu": "2"}}),
            ]
        )
        criteria = _criteria([_req({"cpu": "4"})], job_priority=5, victim_candidates=victims)

        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers(full_agent),
            criteria,
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )

        assert set(computation.selections[0].preempting_session_ids) == {OLD_SESSION, NEW_SESSION}

    async def test_fewest_sessions_prefers_the_agent_needing_fewer_victims(self) -> None:
        agents = [
            _agent("agent-many", {"cpu": "8"}, used={"cpu": "8"}),
            _agent("agent-few", {"cpu": "8"}, used={"cpu": "8"}),
        ]
        small_a = SessionId(uuid.UUID(int=11))
        small_b = SessionId(uuid.UUID(int=12))
        big = SessionId(uuid.UUID(int=13))
        victims = UserVictimCandidates(
            candidates=[
                _victim(small_a, 1, 2020, {"agent-many": {"cpu": "1"}}),
                _victim(small_b, 1, 2021, {"agent-many": {"cpu": "1"}}),
                _victim(big, 1, 2022, {"agent-few": {"cpu": "2"}}),
            ]
        )
        criteria = _criteria([_req({"cpu": "2"})], job_priority=5, victim_candidates=victims)

        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers(agents),
            criteria,
            NO_LIMIT,
            PreemptionOrder.FEWEST_SESSIONS,
        )

        selection = computation.selections[0]
        assert selection.selected_agent.agent_id == AgentId("agent-few")
        assert selection.preempting_session_ids == (big,)

    async def test_reclaim_probe_is_cleared_after_selection(
        self,
        full_agent: list[AgentInfo],
    ) -> None:
        victims = UserVictimCandidates(
            candidates=[_victim(OLD_SESSION, 1, 2020, {"agent-a": {"cpu": "4"}})]
        )
        criteria = _criteria([_req({"cpu": "2"})], job_priority=5, victim_candidates=victims)
        trackers = _trackers(full_agent)

        await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            trackers,
            criteria,
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )

        for tracker in trackers:
            assert tracker.reclaimed_slots == {}
            assert tracker.pending_slots == {}

    async def test_preemption_session_commits_its_reservation(
        self,
        full_agent: list[AgentInfo],
    ) -> None:
        """A session with preemption reserves its resources for real: the
        diffs commit so later sessions see the paper occupancy, while the
        victims' credit is dropped (their resources are not free yet)."""
        victims = UserVictimCandidates(
            candidates=[_victim(OLD_SESSION, 1, 2020, {"agent-a": {"cpu": "4"}})]
        )
        criteria = _criteria([_req({"cpu": "2"})], job_priority=5, victim_candidates=victims)
        trackers = _trackers(full_agent)

        await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            trackers,
            criteria,
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )

        assert trackers[0].committed_slots == _slots({"cpu": "2"})
        assert trackers[0].reclaimed_slots == {}


class TestMultiNodePreemption:
    """The session's claims and allocations stay applied while its own
    requirements are being placed, then the whole state is discarded."""

    async def test_one_victim_admits_both_kernels(self) -> None:
        agents = [_agent("agent-a", {"cpu": "8"}, used={"cpu": "8"})]
        victims = UserVictimCandidates(
            candidates=[_victim(OLD_SESSION, 1, 2020, {"agent-a": {"cpu": "8"}})]
        )
        criteria = _criteria(
            [_req({"cpu": "2"}), _req({"cpu": "2"})],
            job_priority=5,
            victim_candidates=victims,
        )
        trackers = _trackers(agents)

        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            trackers,
            criteria,
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )

        assert len(computation.selections) == 2
        # The first kernel claims the victim; the second fits on the credit
        assert computation.selections[0].preempting_session_ids == (OLD_SESSION,)
        assert computation.selections[1].preempting_session_ids == ()
        # Both kernels' reservations commit; the victim credit is dropped
        assert trackers[0].committed_slots == _slots({"cpu": "4"})
        assert trackers[0].pending_slots == {}
        assert trackers[0].reclaimed_slots == {}

    async def test_claimed_victim_is_not_counted_twice(self) -> None:
        """A victim already claimed by an earlier kernel cannot admit a
        later one again."""
        agents = [_agent("agent-a", {"cpu": "8"}, used={"cpu": "8"})]
        victims = UserVictimCandidates(
            candidates=[_victim(OLD_SESSION, 1, 2020, {"agent-a": {"cpu": "2"}})]
        )
        criteria = _criteria(
            [_req({"cpu": "2"}), _req({"cpu": "2"})],
            job_priority=5,
            victim_candidates=victims,
        )

        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers(agents),
            criteria,
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )

        assert len(computation.failures) == 1
        assert computation.failures[0].requirement_index == 1

    async def test_claimed_victim_credits_its_other_agents(self) -> None:
        """Preempting a multi-node victim frees its allocation everywhere,
        so a later kernel may fit on another agent without a new victim."""
        agents = [
            _agent("agent-a", {"cpu": "8"}, used={"cpu": "8"}),
            _agent("agent-b", {"cpu": "8"}, used={"cpu": "6"}),
        ]
        victims = UserVictimCandidates(
            candidates=[
                _victim(OLD_SESSION, 1, 2020, {"agent-a": {"cpu": "2"}, "agent-b": {"cpu": "2"}})
            ]
        )
        criteria = _criteria(
            [_req({"cpu": "4"}), _req({"cpu": "2"})],
            job_priority=5,
            victim_candidates=victims,
        )

        computation = await _selector().compute_placements(
            AgentSelectionStrategy.CONCENTRATED,
            _trackers(agents),
            criteria,
            NO_LIMIT,
            PreemptionOrder.OLDEST,
        )

        assert len(computation.selections) == 2
        first, second = computation.selections
        # cpu=4 fits only on agent-b with the victim's portion reclaimed
        assert first.selected_agent.agent_id == AgentId("agent-b")
        assert first.preempting_session_ids == (OLD_SESSION,)
        # the victim's agent-a portion is freed by the same preemption
        assert second.selected_agent.agent_id == AgentId("agent-a")
        assert second.preempting_session_ids == ()
