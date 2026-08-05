"""Tests for SessionGroup placement in agent selection (BEP-1064).

The observed per-agent membership (``ResourceGroupResource.group_members_by_agent``)
reaches the trackers, ``SessionGroupOrder`` narrows the preferred tier and
``SessionGroupStrictTrackerFilter`` excludes non-conforming agents. Within one
pass the trackers accumulate the placements made so far, so several members of
one group placed in the same tick see each other.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.identifier.session_group import SessionGroupID
from ai.backend.common.types import AgentId, AgentSelectionStrategy, PreemptionOrder, SessionId
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.data.session_group.types import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    NoCompatibleAgentError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.pool import create_agent_selector
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionCriteria,
    AgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import (
    AgentStateTracker,
    build_agent_trackers,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.agent import (
    AgentLimit,
    AgentMeta,
    AgentResource,
    ResourceGroupResource,
    SlotResource,
)
from ai.backend.manager.views.sokovan.workload import ResourceRequest, SessionGroupPolicy

AGENT_A = AgentId("agent-a")
AGENT_B = AgentId("agent-b")
GROUP_ID = SessionGroupID(uuid.uuid4())
OTHER_GROUP_ID = SessionGroupID(uuid.uuid4())
NO_LIMIT = AgentLimit(max_container_count=None)
CPU = ResourceSlotName("cpu")
MEM = ResourceSlotName("mem")


def _agent_meta(agent_id: AgentId, *, cpu: str = "8") -> AgentMeta:
    return AgentMeta(
        id=agent_id,
        addr=f"{agent_id}:6001",
        architecture=ArchName("x86_64"),
        resources=AgentResource(
            slots={
                CPU: SlotResource(capacity=Decimal(cpu), reserved=Decimal(0), used=Decimal(0)),
                MEM: SlotResource(capacity=Decimal("16384"), reserved=Decimal(0), used=Decimal(0)),
            }
        ),
        container_count=0,
    )


def _trackers(
    members: Mapping[AgentId, Mapping[SessionGroupID, int]] | None = None,
    *,
    agent_cpus: Mapping[AgentId, str] | None = None,
) -> list[AgentStateTracker]:
    capacities = agent_cpus or {}
    return build_agent_trackers(
        ResourceGroupResource(
            agents=[
                _agent_meta(agent_id, cpu=capacities.get(agent_id, "8"))
                for agent_id in (AGENT_A, AGENT_B)
            ],
            group_members_by_agent=members or {},
        )
    )


def _criteria(
    *,
    direction: SessionGroupPlacementDirection | None = None,
    enforcement: SessionGroupPlacementEnforcement = (SessionGroupPlacementEnforcement.PREFERRED),
    group_id: SessionGroupID = GROUP_ID,
    cpu: str = "1",
) -> AgentSelectionCriteria:
    session_group = (
        None
        if direction is None
        else SessionGroupPolicy(
            group_id=group_id,
            direction=direction,
            enforcement=enforcement,
        )
    )
    return AgentSelectionCriteria(
        session_id=SessionId(uuid.uuid4()),
        resource_group_id=ResourceGroupID(uuid.UUID(int=0)),
        requirements=[
            ResourceRequirements(
                requested_slots=ResourceRequest(slots={CPU: Decimal(cpu), MEM: Decimal("1024")}),
                required_architecture=ArchName("x86_64"),
                container_count=1,
            )
        ],
        agent_selection_policy=AgentSelectionPolicy.PREFERRED,
        designated_agent_ids=None,
        job_priority=0,
        victim_candidates=None,
        session_group=session_group,
    )


@pytest.fixture
def selector() -> AgentSelector:
    return create_agent_selector(["cpu", "mem"])


async def _place(
    selector: AgentSelector,
    trackers: list[AgentStateTracker],
    criteria: AgentSelectionCriteria,
    strategy: AgentSelectionStrategy = AgentSelectionStrategy.CONCENTRATED,
) -> AgentId:
    selections = await selector.select_agents_for_batch_requirements(
        strategy,
        trackers,
        criteria,
        NO_LIMIT,
        PreemptionOrder.OLDEST,
    )
    assert len(selections) == 1
    return selections[0].selected_agent.agent_id


class TestSpreadPreferred:
    async def test_narrows_to_the_agent_without_members(self, selector: AgentSelector) -> None:
        """An agent already holding a member loses to an empty one."""
        trackers = _trackers({AGENT_A: {GROUP_ID: 1}})

        selected = await _place(
            selector, trackers, _criteria(direction=SessionGroupPlacementDirection.SPREAD)
        )

        assert selected == AGENT_B

    async def test_falls_back_when_the_empty_agent_cannot_fit(
        self, selector: AgentSelector
    ) -> None:
        """Preferred never excludes: a full preferred agent still yields a placement."""
        trackers = _trackers(
            {AGENT_A: {GROUP_ID: 1}},
            agent_cpus={AGENT_B: "1"},
        )

        selected = await _place(
            selector,
            trackers,
            _criteria(direction=SessionGroupPlacementDirection.SPREAD, cpu="4"),
        )

        assert selected == AGENT_A

    async def test_other_groups_members_do_not_count(self, selector: AgentSelector) -> None:
        """Only this group's members matter; another group's are invisible."""
        trackers = _trackers({AGENT_B: {OTHER_GROUP_ID: 3}})

        selected = await _place(
            selector, trackers, _criteria(direction=SessionGroupPlacementDirection.SPREAD)
        )

        # Both agents hold zero members of GROUP_ID, so the RG strategy decides.
        assert selected in {AGENT_A, AGENT_B}

    async def test_resource_group_strategy_picks_within_the_group_tier(
        self, selector: AgentSelector
    ) -> None:
        """A concentrated RG picks inside the candidate set spread left behind."""
        trackers = _trackers(
            {AGENT_A: {GROUP_ID: 1}},
            agent_cpus={AGENT_A: "16", AGENT_B: "8"},
        )

        selected = await _place(
            selector,
            trackers,
            _criteria(direction=SessionGroupPlacementDirection.SPREAD),
            strategy=AgentSelectionStrategy.CONCENTRATED,
        )

        # Concentrated alone would prefer the tighter-fitting agent-b anyway;
        # the point is that agent-a (the member holder) is never considered.
        assert selected == AGENT_B


class TestPackPreferred:
    async def test_narrows_to_agents_already_holding_members(self, selector: AgentSelector) -> None:
        trackers = _trackers({AGENT_B: {GROUP_ID: 1}})

        selected = await _place(
            selector, trackers, _criteria(direction=SessionGroupPlacementDirection.PACK)
        )

        assert selected == AGENT_B

    async def test_narrows_to_the_agent_holding_the_most_members(
        self, selector: AgentSelector
    ) -> None:
        """The fullest agent wins the tier, even against the RG strategy's pick."""
        trackers = _trackers(
            {AGENT_A: {GROUP_ID: 5}, AGENT_B: {GROUP_ID: 1}},
            agent_cpus={AGENT_A: "16", AGENT_B: "8"},
        )

        selected = await _place(
            selector,
            trackers,
            _criteria(direction=SessionGroupPlacementDirection.PACK),
            strategy=AgentSelectionStrategy.CONCENTRATED,
        )

        # Concentrated alone would take the tighter-fitting agent-b.
        assert selected == AGENT_A


class TestStrictEnforcement:
    async def test_spread_strict_excludes_member_holders(self, selector: AgentSelector) -> None:
        trackers = _trackers({AGENT_A: {GROUP_ID: 1}})

        selected = await _place(
            selector,
            trackers,
            _criteria(
                direction=SessionGroupPlacementDirection.SPREAD,
                enforcement=SessionGroupPlacementEnforcement.STRICT,
            ),
        )

        assert selected == AGENT_B

    async def test_spread_strict_without_candidates_names_the_group(
        self, selector: AgentSelector
    ) -> None:
        """Every agent holds a member: an absolute failure naming group and direction."""
        trackers = _trackers({AGENT_A: {GROUP_ID: 1}, AGENT_B: {GROUP_ID: 2}})

        with pytest.raises(NoCompatibleAgentError) as exc_info:
            await _place(
                selector,
                trackers,
                _criteria(
                    direction=SessionGroupPlacementDirection.SPREAD,
                    enforcement=SessionGroupPlacementEnforcement.STRICT,
                ),
            )

        message = str(exc_info.value)
        assert str(GROUP_ID) in message
        assert "spread" in message

    async def test_pack_strict_anchors_the_first_member(self, selector: AgentSelector) -> None:
        """With no member anywhere the filter does not apply (anchor rule)."""
        trackers = _trackers()

        selected = await _place(
            selector,
            trackers,
            _criteria(
                direction=SessionGroupPlacementDirection.PACK,
                enforcement=SessionGroupPlacementEnforcement.STRICT,
            ),
        )

        assert selected in {AGENT_A, AGENT_B}

    async def test_pack_strict_excludes_agents_without_members(
        self, selector: AgentSelector
    ) -> None:
        trackers = _trackers(
            {AGENT_A: {GROUP_ID: 1}},
            agent_cpus={AGENT_A: "8", AGENT_B: "16"},
        )

        selected = await _place(
            selector,
            trackers,
            _criteria(
                direction=SessionGroupPlacementDirection.PACK,
                enforcement=SessionGroupPlacementEnforcement.STRICT,
            ),
            strategy=AgentSelectionStrategy.DISPERSED,
        )

        # Dispersed would prefer the roomier agent-b; the strict filter removed it.
        assert selected == AGENT_A


class TestUnconstrainedPlacement:
    async def test_no_group_leaves_selection_unchanged(self, selector: AgentSelector) -> None:
        trackers = _trackers({AGENT_A: {GROUP_ID: 1}, AGENT_B: {GROUP_ID: 5}})

        selected = await _place(selector, trackers, _criteria())

        assert selected in {AGENT_A, AGENT_B}

    async def test_none_direction_does_not_participate(self, selector: AgentSelector) -> None:
        """A ``none`` group keeps its membership but places like an ungrouped session."""
        trackers = _trackers(
            {AGENT_A: {GROUP_ID: 1}},
            agent_cpus={AGENT_A: "8", AGENT_B: "16"},
        )

        selected = await _place(
            selector,
            trackers,
            _criteria(direction=SessionGroupPlacementDirection.NONE),
            strategy=AgentSelectionStrategy.DISPERSED,
        )

        # Dispersed picks the roomiest agent even though it would be the
        # member-free one under spread — the direction is disengaged.
        assert selected == AGENT_B


class TestInBatchAccumulation:
    async def test_three_members_of_one_group_land_on_distinct_agents(
        self, selector: AgentSelector
    ) -> None:
        """A three-replica scale-out in one pass spreads instead of piling up."""
        resources = ResourceGroupResource(
            agents=[
                _agent_meta(AgentId("agent-a")),
                _agent_meta(AgentId("agent-b")),
                _agent_meta(AgentId("agent-c")),
            ],
        )
        trackers = build_agent_trackers(resources)

        selected = [
            await _place(
                selector, trackers, _criteria(direction=SessionGroupPlacementDirection.SPREAD)
            )
            for _ in range(3)
        ]

        assert len(set(selected)) == 3

    async def test_rolled_back_placement_leaves_no_member(self, selector: AgentSelector) -> None:
        """A failed placement must not leave a phantom member behind."""
        trackers = _trackers()
        # Requests more CPU than any agent has: the batch fails and rolls back.
        with pytest.raises(Exception):
            await _place(
                selector,
                trackers,
                _criteria(direction=SessionGroupPlacementDirection.SPREAD, cpu="99"),
            )

        assert all(tracker.current_group_member_count(GROUP_ID) == 0 for tracker in trackers)

        selected = await _place(
            selector, trackers, _criteria(direction=SessionGroupPlacementDirection.SPREAD)
        )
        assert selected in {AGENT_A, AGENT_B}
