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
    """Test that failed agents are deprioritized during agent selection."""

    async def test_failed_agent_is_avoided(
        self,
        agents: list[AgentInfo],
        selection_config: AgentSelectionConfig,
        concentrated_selector: AgentSelector,
    ) -> None:
        """When one agent has failed, the other agent should be selected."""
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
        """When all compatible agents have failed, all should remain available."""
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
        """When no agents have failed, selection proceeds normally."""
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
        """Designated agents should be selected even if they previously failed."""
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
        """Failed agent filtering works with dispersed strategy too."""
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
        """Failed agent IDs not present in the agent pool are safely ignored."""
        criteria = _make_criteria_with_failed_agents(
            failed_agent_ids=frozenset({AgentId("agent-nonexistent")})
        )

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            agents, criteria, selection_config
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id in {AGENT_A, AGENT_B}
