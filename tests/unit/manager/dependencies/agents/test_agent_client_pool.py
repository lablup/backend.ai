from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.dependencies.agents.agent_client_pool import (
    AgentClientPoolDependency,
    AgentClientPoolInput,
)


class TestAgentClientPoolDependency:
    """Test AgentClientPoolDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.agents.agent_client_pool.AgentClientPool")
    async def test_provide_agent_client_pool(
        self,
        mock_pool_class: MagicMock,
    ) -> None:
        """Dependency should create agent client pool and close on cleanup."""
        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_pool_class.return_value = mock_pool

        setup_input = AgentClientPoolInput(
            agent_cache=MagicMock(),
        )

        dependency = AgentClientPoolDependency()
        async with dependency.provide(setup_input) as pool:
            assert pool is mock_pool
            mock_pool_class.assert_called_once()
            mock_pool.close.assert_not_called()

        mock_pool.close.assert_awaited_once()
