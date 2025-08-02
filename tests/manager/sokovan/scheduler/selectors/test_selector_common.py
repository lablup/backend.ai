"""Test common functionality of AgentSelector."""

from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.sokovan.scheduler.selectors.legacy import LegacyAgentSelector
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentSelector

from .conftest import create_agent_info, create_selection_criteria


class TestAgentSelectorCommon:
    """Test common filtering and selection logic."""

    @pytest.mark.asyncio
    async def test_empty_agent_list(self):
        """Test handling of empty agent list."""
        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        result = await selector.select_agent([], criteria)
        assert result is None

    @pytest.mark.asyncio
    async def test_architecture_filtering(self):
        """Test that agents with incompatible architectures are filtered out."""
        agents = [
            create_agent_info(agent_id="x86-agent", architecture="x86_64"),
            create_agent_info(agent_id="arm-agent", architecture="aarch64"),
        ]

        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(architecture="x86_64")

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("x86-agent")

    @pytest.mark.asyncio
    async def test_resource_availability_filtering(self):
        """Test that agents without enough resources are filtered out."""
        agents = [
            create_agent_info(
                agent_id="busy-agent",
                available_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
                occupied_slots={"cpu": Decimal("1.5"), "mem": Decimal("3072")},
            ),
            create_agent_info(
                agent_id="free-agent",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("1"), "mem": Decimal("2048")},
            ),
        ]

        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(
            requested_slots={"cpu": Decimal("2"), "mem": Decimal("4096")}
        )

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("free-agent")

    @pytest.mark.asyncio
    async def test_container_limit_filtering(self):
        """Test that agents exceeding container limit are filtered out."""
        agents = [
            create_agent_info(agent_id="full-agent", container_count=10),
            create_agent_info(agent_id="available-agent", container_count=5),
        ]

        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(max_container_count=8)

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("available-agent")

    @pytest.mark.asyncio
    async def test_designated_agent_selection(self):
        """Test that designated agent is selected if available and compatible."""
        agents = [
            create_agent_info(agent_id="agent-1"),
            create_agent_info(agent_id="designated-agent"),
            create_agent_info(agent_id="agent-3"),
        ]

        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(designated_agent_id="designated-agent")

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("designated-agent")

    @pytest.mark.asyncio
    async def test_designated_agent_not_compatible(self):
        """Test that incompatible designated agent is not selected."""
        agents = [
            create_agent_info(
                agent_id="designated-agent",
                available_slots={"cpu": Decimal("1"), "mem": Decimal("512")},
                occupied_slots={"cpu": Decimal("0.5"), "mem": Decimal("256")},
            ),
            create_agent_info(agent_id="compatible-agent"),
        ]

        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(
            designated_agent_id="designated-agent",
            requested_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
        )

        result = await selector.select_agent(agents, criteria)
        assert result is None

    @pytest.mark.asyncio
    async def test_designated_agent_not_in_list(self):
        """Test that missing designated agent returns None."""
        agents = [
            create_agent_info(agent_id="agent-1"),
            create_agent_info(agent_id="agent-2"),
        ]

        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(designated_agent_id="non-existent-agent")

        result = await selector.select_agent(agents, criteria)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_agents_meet_criteria(self):
        """Test when no agents meet all criteria."""
        agents = [
            create_agent_info(
                agent_id="small-agent",
                available_slots={"cpu": Decimal("2"), "mem": Decimal("2048")},
            ),
            create_agent_info(
                agent_id="wrong-arch",
                architecture="aarch64",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            ),
        ]

        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(
            requested_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            architecture="x86_64",
        )

        result = await selector.select_agent(agents, criteria)
        assert result is None
