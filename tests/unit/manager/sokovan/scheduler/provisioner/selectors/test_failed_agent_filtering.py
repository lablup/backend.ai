"""Tests for failed agent deprioritization in agent selection."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
    DispersedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentInfo,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentSelector,
    KernelResourceSpec,
    SessionMetadata,
)

# Named constants for agent IDs used across tests
AGENT_A = AgentId("agent-a")
AGENT_B = AgentId("agent-b")


def _make_agent(agent_id: str) -> AgentInfo:
    return AgentInfo(
        agent_id=AgentId(agent_id),
        agent_addr=f"{agent_id}:6001",
        architecture="x86_64",
        available_slots=ResourceSlot({"cpu": Decimal("8"), "mem": Decimal("16384")}),
        occupied_slots=ResourceSlot({"cpu": Decimal("0"), "mem": Decimal("0")}),
        scaling_group="default",
        container_count=0,
    )


def _make_criteria_with_failed_agents(
    failed_agent_ids: frozenset[AgentId] | None = None,
) -> AgentSelectionCriteria:
    """Build AgentSelectionCriteria for failed-agent filtering tests.

    Only failed_agent_ids varies between tests — all other fields are fixed boilerplate.
    """
    kernel_id = uuid.uuid4()
    return AgentSelectionCriteria(
        session_metadata=SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.INTERACTIVE,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        ),
        kernel_requirements={
            kernel_id: KernelResourceSpec(
                requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                required_architecture="x86_64",
            ),
        },
        failed_agent_ids=failed_agent_ids or frozenset(),
    )


@pytest.fixture
def agents() -> list[AgentInfo]:
    return [_make_agent("agent-a"), _make_agent("agent-b")]


@pytest.fixture
def selection_config() -> AgentSelectionConfig:
    return AgentSelectionConfig(max_container_count=None)


@pytest.fixture
def concentrated_selector() -> AgentSelector:
    return AgentSelector(ConcentratedAgentSelector(["cpu", "mem"]))


@pytest.fixture
def dispersed_selector() -> AgentSelector:
    return AgentSelector(DispersedAgentSelector(["cpu", "mem"]))


class TestFailedAgentFiltering:
    """Tests for the failed agent deprioritization pass in agent selection.

    When a session fails to start on an agent (kernel creation RPC error, timeout, etc.),
    that agent is recorded in Valkey as a "failed agent" for that session. On retry,
    the selector reads these records and excludes the failed agents from the candidate
    pool before passing it to the placement strategy (concentrated/dispersed).

    Pool: agent-a, agent-b (both have sufficient resources for all tests)
    """

    async def test_failed_agent_is_avoided(
        self,
        agents: list[AgentInfo],
        selection_config: AgentSelectionConfig,
        concentrated_selector: AgentSelector,
    ) -> None:
        """Basic filtering: a previously-failed agent is excluded from selection.

        Scenario:
          - agent-a failed on the previous start attempt for this session
          - agent-b has not failed
        Expected:
          - agent-a is removed from the candidate pool
          - agent-b is selected
        """
        criteria = _make_criteria_with_failed_agents(failed_agent_ids=frozenset({AGENT_A}))

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            agents, criteria, selection_config
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AGENT_B

    async def test_all_agents_failed_fallback(
        self,
        agents: list[AgentInfo],
        selection_config: AgentSelectionConfig,
        concentrated_selector: AgentSelector,
    ) -> None:
        """Fallback: when every compatible agent has failed, the filter is skipped.

        Scenario:
          - Both agent-a and agent-b previously failed for this session
          - No other agents are available
        Expected:
          - Filtering is skipped (removing all agents would block scheduling entirely)
          - One of the two agents is selected anyway, allowing the session to proceed
        """
        criteria = _make_criteria_with_failed_agents(failed_agent_ids=frozenset({AGENT_A, AGENT_B}))

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            agents, criteria, selection_config
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id in {AGENT_A, AGENT_B}

    async def test_no_failed_agents_no_change(
        self,
        agents: list[AgentInfo],
        selection_config: AgentSelectionConfig,
        concentrated_selector: AgentSelector,
    ) -> None:
        """No-op: an empty failed_agent_ids set leaves selection unchanged.

        Scenario:
          - First scheduling attempt — no prior failures recorded
          - failed_agent_ids is empty
        Expected:
          - The filtering pass has no effect
          - Normal selection proceeds and returns one agent
        """
        criteria = _make_criteria_with_failed_agents(failed_agent_ids=frozenset())

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            agents, criteria, selection_config
        )

        assert len(selections) == 1

    async def test_designated_agent_overrides_failed_filter(
        self,
        agents: list[AgentInfo],
        selection_config: AgentSelectionConfig,
        concentrated_selector: AgentSelector,
    ) -> None:
        """Designated agent takes precedence over the failed-agent filter.

        Scenario:
          - The user explicitly designated agent-a for this session
          - agent-a also appears in failed_agent_ids from a prior attempt
        Expected:
          - The designated-agent check runs before the failed-agent filter
          - agent-a is returned as-is, respecting the user's explicit choice
        """
        criteria = _make_criteria_with_failed_agents(failed_agent_ids=frozenset({AGENT_A}))

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            agents,
            criteria,
            selection_config,
            designated_agent_ids=[AGENT_A],
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AGENT_A

    async def test_failed_filter_works_with_dispersed_strategy(
        self,
        agents: list[AgentInfo],
        selection_config: AgentSelectionConfig,
        dispersed_selector: AgentSelector,
    ) -> None:
        """Failed-agent filtering is strategy-agnostic (dispersed policy).

        Scenario:
          - agent-a previously failed for this session
          - The scaling group uses dispersed (spread) placement policy
        Expected:
          - agent-a is excluded from the candidate pool before the strategy runs
          - agent-b is selected regardless of the placement policy
        This verifies that filtering happens upstream of the strategy, not inside it.
        """
        criteria = _make_criteria_with_failed_agents(failed_agent_ids=frozenset({AGENT_A}))

        selections = await dispersed_selector.select_agents_for_batch_requirements(
            agents, criteria, selection_config
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AGENT_B

    async def test_failed_agent_not_in_pool_is_ignored(
        self,
        agents: list[AgentInfo],
        selection_config: AgentSelectionConfig,
        concentrated_selector: AgentSelector,
    ) -> None:
        """Stale record: a failed agent ID that no longer exists in the pool is harmless.

        Scenario:
          - Valkey contains a failed_agent_id for "agent-nonexistent"
            (e.g. the agent was removed from the cluster after the failure was recorded)
          - The current pool contains only agent-a and agent-b
        Expected:
          - The nonexistent ID has no effect on the candidate pool
          - Normal selection proceeds and returns one of the two available agents
        """
        criteria = _make_criteria_with_failed_agents(
            failed_agent_ids=frozenset({AgentId("agent-nonexistent")})
        )

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            agents, criteria, selection_config
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id in {AGENT_A, AGENT_B}
