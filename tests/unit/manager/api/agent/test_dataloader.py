"""Tests for agent GraphQL DataLoader utilities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.types import AgentId
from ai.backend.manager.api.gql.data_loader.agent.loader import load_agents_by_ids
from ai.backend.manager.data.agent.types import AgentDetailData


class TestLoadAgentsByIds:
    """Tests for load_agents_by_ids function."""

    @staticmethod
    def create_mock_agent_detail(agent_id: AgentId) -> MagicMock:
        mock = MagicMock(spec=AgentDetailData)
        mock.agent = MagicMock()
        mock.agent.id = agent_id
        return mock

    @staticmethod
    def create_mock_processor(agents: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.agents = agents
        mock_processor.search_agents.wait_for_complete = AsyncMock(return_value=mock_action_result)
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_agents_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_agents.wait_for_complete.assert_not_called()

    async def test_returns_agents_in_request_order(self) -> None:
        # Given
        id1 = AgentId("agent-1")
        id2 = AgentId("agent-2")
        id3 = AgentId("agent-3")
        agent1 = self.create_mock_agent_detail(id1)
        agent2 = self.create_mock_agent_detail(id2)
        agent3 = self.create_mock_agent_detail(id3)
        mock_processor = self.create_mock_processor(
            [agent3, agent1, agent2]  # DB returns in different order
        )

        # When
        result = await load_agents_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [agent1, agent2, agent3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = AgentId("existing-agent")
        missing_id = AgentId("missing-agent")
        existing_agent = self.create_mock_agent_detail(existing_id)
        mock_processor = self.create_mock_processor([existing_agent])

        # When
        result = await load_agents_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_agent, None]
