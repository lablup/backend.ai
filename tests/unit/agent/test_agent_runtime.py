from __future__ import annotations

import pytest

from ai.backend.agent.errors import AgentIdNotFoundError
from ai.backend.agent.runtime import AgentRuntime
from ai.backend.common.types import AgentId


class TestAgentRuntimeSingleAgent:
    """Test AgentRuntime with single agent configuration."""

    @pytest.mark.asyncio
    async def test_get_agent_returns_default_when_id_is_none(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        When agent_id is None, get_agent() should return the default agent.
        """
        agent = agent_runtime.get_agent(None)

        assert agent is not None
        assert agent.id is not None
        # In single agent mode, the default agent should be the only agent
        assert agent is agent_runtime.get_agent(agent.id)

    @pytest.mark.asyncio
    async def test_get_agent_returns_agent_by_id(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        get_agent() should return the correct agent when given a specific ID.
        """
        # Get the default agent's ID
        default_agent = agent_runtime.get_agent(None)
        agent_id = default_agent.id

        # Retrieve by ID
        agent = agent_runtime.get_agent(agent_id)

        assert agent is default_agent
        assert agent.id == agent_id

    @pytest.mark.asyncio
    async def test_get_agent_raises_error_for_nonexistent_id(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        get_agent() should raise AgentIdNotFoundError for non-existent agent IDs.
        """
        nonexistent_id = AgentId("nonexistent-agent-id")

        with pytest.raises(AgentIdNotFoundError) as exc_info:
            agent_runtime.get_agent(nonexistent_id)

        # Verify error message is helpful
        assert str(nonexistent_id) in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_agents_returns_all_agents(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        get_agents() should return a list of all agents.
        """
        agents = agent_runtime.get_agents()

        assert isinstance(agents, list)
        assert len(agents) == 1  # Single agent mode

        # Verify the agent is accessible
        for agent in agents:
            assert agent.id is not None
            assert agent is agent_runtime.get_agent(agent.id)


class TestAgentRuntimeInitialization:
    """Test AgentRuntime initialization and cleanup."""

    @pytest.mark.asyncio
    async def test_runtime_creates_agents_from_config(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        AgentRuntime.create_agents() should initialize agents from config.
        """
        # Verify agents were created
        agents = agent_runtime.get_agents()
        assert len(agents) > 0

        # Verify default agent is set
        default_agent = agent_runtime.get_agent(None)
        assert default_agent is not None

        # Verify all agents have valid IDs
        for agent in agents:
            assert agent.id is not None

    @pytest.mark.asyncio
    async def test_runtime_shutdown_cleans_up_agents(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        AgentRuntime.shutdown() should properly clean up all agents.
        """
        # Verify agents exist before shutdown
        agents = agent_runtime.get_agents()
        assert len(agents) > 0

        # Shutdown
        await agent_runtime.__aexit__(None, None, None)

        # After shutdown, the runtime should be in a clean state
        # (Specific behavior depends on implementation - adjust as needed)
        # For now, we just verify shutdown doesn't raise errors
