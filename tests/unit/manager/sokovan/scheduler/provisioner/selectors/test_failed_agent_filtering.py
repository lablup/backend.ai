"""Tests for failed agent deprioritization in agent selection."""

from __future__ import annotations

import uuid
from decimal import Decimal

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
    ResourceRequirements,
    SessionMetadata,
)


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


def _make_criteria(
    failed_agent_ids: frozenset[AgentId] | None = None,
) -> AgentSelectionCriteria:
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


def _make_config() -> AgentSelectionConfig:
    return AgentSelectionConfig(max_container_count=None)


def _make_resource_req() -> ResourceRequirements:
    return ResourceRequirements(
        kernel_ids=[uuid.uuid4()],
        requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
        required_architecture="x86_64",
    )


class TestFailedAgentFiltering:
    """Test that failed agents are deprioritized during agent selection."""

    async def test_failed_agent_is_avoided(self) -> None:
        """When one agent has failed, the other agent should be selected."""
        agents = [_make_agent("agent-a"), _make_agent("agent-b")]
        criteria = _make_criteria(failed_agent_ids=frozenset({AgentId("agent-a")}))

        selector = AgentSelector(ConcentratedAgentSelector(["cpu", "mem"]))
        selections = await selector.select_agents_for_batch_requirements(
            agents, criteria, _make_config()
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AgentId("agent-b")

    async def test_all_agents_failed_fallback(self) -> None:
        """When all compatible agents have failed, all should remain available."""
        agents = [_make_agent("agent-a"), _make_agent("agent-b")]
        criteria = _make_criteria(
            failed_agent_ids=frozenset({AgentId("agent-a"), AgentId("agent-b")})
        )

        selector = AgentSelector(ConcentratedAgentSelector(["cpu", "mem"]))
        selections = await selector.select_agents_for_batch_requirements(
            agents, criteria, _make_config()
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id in {AgentId("agent-a"), AgentId("agent-b")}

    async def test_no_failed_agents_no_change(self) -> None:
        """When no agents have failed, selection proceeds normally."""
        agents = [_make_agent("agent-a"), _make_agent("agent-b")]
        criteria = _make_criteria(failed_agent_ids=frozenset())

        selector = AgentSelector(ConcentratedAgentSelector(["cpu", "mem"]))
        selections = await selector.select_agents_for_batch_requirements(
            agents, criteria, _make_config()
        )

        assert len(selections) == 1

    async def test_designated_agent_overrides_failed_filter(self) -> None:
        """Designated agents should be selected even if they previously failed."""
        agents = [_make_agent("agent-a"), _make_agent("agent-b")]
        criteria = _make_criteria(failed_agent_ids=frozenset({AgentId("agent-a")}))

        selector = AgentSelector(ConcentratedAgentSelector(["cpu", "mem"]))
        selections = await selector.select_agents_for_batch_requirements(
            agents,
            criteria,
            _make_config(),
            designated_agent_ids=[AgentId("agent-a")],
        )

        # Designated agent takes precedence over failed agent filter
        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AgentId("agent-a")

    async def test_failed_filter_works_with_dispersed_strategy(self) -> None:
        """Failed agent filtering works with dispersed strategy too."""
        agents = [_make_agent("agent-a"), _make_agent("agent-b")]
        criteria = _make_criteria(failed_agent_ids=frozenset({AgentId("agent-a")}))

        selector = AgentSelector(DispersedAgentSelector(["cpu", "mem"]))
        selections = await selector.select_agents_for_batch_requirements(
            agents, criteria, _make_config()
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AgentId("agent-b")

    async def test_failed_agent_not_in_pool_is_ignored(self) -> None:
        """Failed agent IDs not present in the agent pool are safely ignored."""
        agents = [_make_agent("agent-a"), _make_agent("agent-b")]
        criteria = _make_criteria(failed_agent_ids=frozenset({AgentId("agent-nonexistent")}))

        selector = AgentSelector(ConcentratedAgentSelector(["cpu", "mem"]))
        selections = await selector.select_agents_for_batch_requirements(
            agents, criteria, _make_config()
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id in {AgentId("agent-a"), AgentId("agent-b")}
