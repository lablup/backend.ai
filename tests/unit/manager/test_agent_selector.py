from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from uuid import uuid4

import pytest

from ai.backend.common.types import (
    AgentId,
    AgentSelectionStrategy,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.scheduler.agent_selector import (
    ConcentratedAgentSelector,
    RoundRobinAgentSelector,
)
from ai.backend.manager.scheduler.fifo import FIFOSlotScheduler
from ai.backend.manager.scheduler.types import InMemoryResourceGroupStateStore

from .scheduler_utils import (
    agent_selection_resource_priority,
    create_mock_agent,
    create_mock_session,
    find_and_pop_picked_session,
    update_agent_assignment,
)


@pytest.mark.asyncio
async def test_agent_selection_strategy_rr() -> None:
    example_homogeneous_agents = [
        create_mock_agent(
            AgentId(f"i-{idx:03d}"),
            available_slots=ResourceSlot({
                "cpu": Decimal("4.0"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("4.0"),
                "rocm.devices": Decimal("2"),
            }),
        )
        for idx in range(10)
    ]
    example_homogeneous_pending_sessions = [
        create_mock_session(
            SessionId(uuid4()),
            requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("1024")}),
        )
        for _ in range(20)
    ]

    sgroup_opts = ScalingGroupOpts(
        agent_selection_strategy=AgentSelectionStrategy.ROUNDROBIN,
    )
    scheduler = FIFOSlotScheduler(
        sgroup_opts,
        {},
    )

    agstate_cls = RoundRobinAgentSelector.get_state_cls()
    agselector = RoundRobinAgentSelector(
        sgroup_opts,
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )

    num_agents = len(example_homogeneous_agents)
    total_capacity = sum((ag.available_slots for ag in example_homogeneous_agents), ResourceSlot())
    agent_ids = []
    # Repeat the allocation for two iterations
    for _ in range(num_agents * 2):
        picked_session_id = scheduler.pick_session(
            total_capacity,
            example_homogeneous_pending_sessions,
            [],
        )
        assert picked_session_id == example_homogeneous_pending_sessions[0].id
        picked_session = find_and_pop_picked_session(
            example_homogeneous_pending_sessions,
            picked_session_id,
        )
        agent_ids.append(
            await agselector.assign_agent_for_session(
                example_homogeneous_agents,
                picked_session,
            )
        )
    assert agent_ids == [AgentId(f"i-{idx:03d}") for idx in range(num_agents)] * 2


@pytest.mark.asyncio
async def test_agent_selection_strategy_rr_skip_unacceptable_agents() -> None:
    agents: Sequence[AgentRow] = [
        create_mock_agent(
            AgentId("i-001"),
            available_slots=ResourceSlot({"cpu": Decimal("8"), "mem": Decimal("4096")}),
        ),
        create_mock_agent(
            AgentId("i-002"),
            available_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("2048")}),
        ),
        create_mock_agent(
            AgentId("i-003"),
            available_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("1024")}),
        ),
        create_mock_agent(
            AgentId("i-004"),
            available_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("512")}),
        ),
    ]
    pending_sessions = [
        create_mock_session(
            SessionId(uuid4()),
            ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("500")}),
        )
        for _ in range(8)
    ]
    # Expected result:
    # i-001 can accommodate 4 sessions.
    # i-002 can accommodate 2 sessions.
    # i-003 can accommodate 1 sessions.
    # i-004 can accommodate 0 sessions.

    sgroup_opts = ScalingGroupOpts(
        agent_selection_strategy=AgentSelectionStrategy.ROUNDROBIN,
    )
    scheduler = FIFOSlotScheduler(
        sgroup_opts,
        {},
    )

    agstate_cls = RoundRobinAgentSelector.get_state_cls()
    agselector = RoundRobinAgentSelector(
        sgroup_opts,
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )

    total_capacity = sum((ag.available_slots for ag in agents), ResourceSlot())

    results: list[tuple[AgentId | None, SessionId]] = []
    scheduled_sessions: list[SessionRow] = []

    for _ in range(8):
        picked_session_id = scheduler.pick_session(
            total_capacity,
            pending_sessions,
            scheduled_sessions,
        )
        assert picked_session_id is not None
        picked_session = find_and_pop_picked_session(
            pending_sessions,
            picked_session_id,
        )
        # Bookkeeping picked_session in scheduled_sessions should be skipped if we fail to
        # assign an agent, but we keep it here for the validation step of this test case.
        scheduled_sessions.append(picked_session)
        picked_agent_id = await agselector.assign_agent_for_session(
            agents,
            picked_session,
        )
        if picked_agent_id is not None:
            update_agent_assignment(agents, picked_agent_id, picked_session.requested_slots)
        results.append((picked_agent_id, picked_session_id))

    print()
    for ag in agents:
        print(
            ag.id,
            f"{ag.occupied_slots['cpu']}/{ag.available_slots['cpu']}",
            f"{ag.occupied_slots['mem']}/{ag.available_slots['mem']}",
        )
    # As more sessions have the assigned agents, the remaining capacity diminishes
    # and the range of round-robin also becomes limited.
    # When there is no assignable agent, it should return None.
    assert len(results) == 8
    assert results == [
        ("i-001", scheduled_sessions[0].id),
        ("i-002", scheduled_sessions[1].id),
        ("i-003", scheduled_sessions[2].id),
        ("i-001", scheduled_sessions[3].id),
        ("i-002", scheduled_sessions[4].id),
        ("i-001", scheduled_sessions[5].id),
        ("i-001", scheduled_sessions[6].id),
        (None, scheduled_sessions[7].id),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "agents": [
                {"id": "i-001", "available_slots": {"cpu": "1", "mem": "512"}},
                {"id": "i-002", "available_slots": {"cpu": "4", "mem": "2048"}},
                {"id": "i-003", "available_slots": {"cpu": "4", "mem": "2048"}},
            ],
            "kernel_counts_at_same_endpoint": {},
            "picked_agent": "i-001",
        },
        {
            "agents": [
                {"id": "i-001", "available_slots": {"cpu": "1", "mem": "512"}},
                {"id": "i-002", "available_slots": {"cpu": "4", "mem": "2048"}},
                {"id": "i-003", "available_slots": {"cpu": "4", "mem": "2048"}},
            ],
            "kernel_counts_at_same_endpoint": {"i-001": 1, "i-002": 1},
            "picked_agent": "i-003",
        },
        {
            "agents": [
                {"id": "i-001", "available_slots": {"cpu": "1", "mem": "512"}},
                {"id": "i-002", "available_slots": {"cpu": "4", "mem": "2048"}},
                {"id": "i-003", "available_slots": {"cpu": "4", "mem": "2048"}},
            ],
            "kernel_counts_at_same_endpoint": {"i-001": 2, "i-002": 1, "i-003": 2},
            "picked_agent": "i-002",
        },
    ],
    ids=[
        "When there is no session assigned to the same endpoint, ConcentratedAgentSelector should pick the agent with the least resources",
        "When there are sessions assigned to the same endpoint, the new pending session should be assigned to an agent with the fewest kernel allocations. (1)",
        "When there are sessions assigned to the same endpoint, the new pending session should be assigned to an agent with the fewest kernel allocations. (2)",
    ],
)
async def test_enforce_spreading_endpoint_replica(test_case) -> None:
    agents: Sequence[AgentRow] = [
        create_mock_agent(
            AgentId(agent["id"]),
            available_slots=ResourceSlot({
                k: Decimal(v) for k, v in agent["available_slots"].items()
            }),
        )
        for agent in test_case["agents"]
    ]

    sgroup_opts = ScalingGroupOpts(
        agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED,
        enforce_spreading_endpoint_replica=True,
    )

    config = {
        "kernel_counts_at_same_endpoint": test_case["kernel_counts_at_same_endpoint"],
    }

    agstate_cls = ConcentratedAgentSelector.get_state_cls()
    ag_selector = ConcentratedAgentSelector(
        sgroup_opts,
        config,
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )

    mock_session = create_mock_session(
        SessionId(uuid4()),
        ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("100")}),
        session_type=SessionTypes.INFERENCE,
    )

    picked_agent = await ag_selector.select_agent(agents, mock_session)
    assert picked_agent == test_case["picked_agent"]
