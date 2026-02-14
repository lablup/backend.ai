from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.dependencies.agents.registry import (
    AgentRegistryDependency,
    AgentRegistryInput,
)


class TestAgentRegistryDependency:
    """Test AgentRegistryDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.agents.registry.AgentRegistry")
    async def test_provide_agent_registry(
        self,
        mock_registry_class: MagicMock,
    ) -> None:
        """Dependency should create registry, call init(), and shutdown() on cleanup."""
        mock_registry = MagicMock()
        mock_registry.init = AsyncMock()
        mock_registry.shutdown = AsyncMock()
        mock_registry_class.return_value = mock_registry

        setup_input = AgentRegistryInput(
            config_provider=MagicMock(),
            db=MagicMock(),
            agent_cache=MagicMock(),
            agent_client_pool=MagicMock(),
            valkey_stat=MagicMock(),
            valkey_live=MagicMock(),
            valkey_image=MagicMock(),
            event_producer=MagicMock(),
            event_hub=MagicMock(),
            storage_manager=MagicMock(),
            hook_plugin_ctx=MagicMock(),
            network_plugin_ctx=MagicMock(),
            scheduling_controller=MagicMock(),
            debug=False,
            manager_public_key=MagicMock(),
            manager_secret_key=MagicMock(),
        )

        dependency = AgentRegistryDependency()
        async with dependency.provide(setup_input) as registry:
            assert registry is mock_registry
            mock_registry_class.assert_called_once()
            mock_registry.init.assert_awaited_once()
            mock_registry.shutdown.assert_not_called()

        mock_registry.shutdown.assert_awaited_once()
