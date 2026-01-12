from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.dependencies.stacks.builder import DependencyBuilderStack
from ai.backend.common.typed_validators import CommaSeparatedStrList
from ai.backend.web.dependencies.components.composer import (
    ComponentComposer,
    ComponentResources,
)
from ai.backend.web.dependencies.components.hive_router_client import HiveRouterClientInfo
from ai.backend.web.dependencies.components.manager_client import ManagerClientInfo


@dataclass
class MockAPIConfig:
    """Mock for API configuration."""

    endpoint: CommaSeparatedStrList
    ssl_verify: bool
    connection_limit: int


@dataclass
class MockApolloRouterConfig:
    """Mock for Apollo Router configuration."""

    enabled: bool
    endpoints: CommaSeparatedStrList


@dataclass
class MockConfig:
    """Mock for web server config."""

    api: MockAPIConfig
    apollo_router: MockApolloRouterConfig


class TestComponentComposer:
    """Test ComponentComposer lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.web.dependencies.components.manager_client.ClientPool")
    @patch("ai.backend.web.dependencies.components.hive_router_client.ClientPool")
    async def test_compose_with_hive_router_enabled(
        self,
        mock_hive_pool_class: MagicMock,
        mock_manager_pool_class: MagicMock,
    ) -> None:
        """Composer should setup both manager and hive router when enabled."""
        config = MockConfig(
            api=MockAPIConfig(
                endpoint=CommaSeparatedStrList("http://127.0.0.1:8081"),
                ssl_verify=True,
                connection_limit=100,
            ),
            apollo_router=MockApolloRouterConfig(
                enabled=True,
                endpoints=CommaSeparatedStrList("http://router:4000"),
            ),
        )

        # Mock client pools
        mock_manager_pool = MagicMock()
        mock_manager_pool.close = AsyncMock()
        mock_manager_pool_class.return_value = mock_manager_pool

        mock_hive_pool = MagicMock()
        mock_hive_pool.close = AsyncMock()
        mock_hive_pool_class.return_value = mock_hive_pool

        composer = ComponentComposer()
        stack = DependencyBuilderStack()

        async with stack:
            async with composer.compose(stack, config) as resources:  # type: ignore[arg-type]
                assert isinstance(resources, ComponentResources)
                assert isinstance(resources.manager_client, ManagerClientInfo)
                assert resources.manager_client.client_pool is mock_manager_pool
                assert resources.manager_client.endpoints == config.api.endpoint

                assert isinstance(resources.hive_router_client, HiveRouterClientInfo)
                assert resources.hive_router_client.client_pool is mock_hive_pool
                assert resources.hive_router_client.endpoints == config.apollo_router.endpoints

    @pytest.mark.asyncio
    @patch("ai.backend.web.dependencies.components.manager_client.ClientPool")
    @patch("ai.backend.web.dependencies.components.hive_router_client.ClientPool")
    async def test_compose_with_hive_router_disabled(
        self,
        mock_hive_pool_class: MagicMock,
        mock_manager_pool_class: MagicMock,
    ) -> None:
        """Composer should only setup manager when hive router is disabled."""
        config = MockConfig(
            api=MockAPIConfig(
                endpoint=CommaSeparatedStrList("http://127.0.0.1:8081"),
                ssl_verify=True,
                connection_limit=100,
            ),
            apollo_router=MockApolloRouterConfig(
                enabled=False,
                endpoints=CommaSeparatedStrList("http://router:4000"),
            ),
        )

        # Mock client pools
        mock_manager_pool = MagicMock()
        mock_manager_pool.close = AsyncMock()
        mock_manager_pool_class.return_value = mock_manager_pool

        composer = ComponentComposer()
        stack = DependencyBuilderStack()

        async with stack:
            async with composer.compose(stack, config) as resources:  # type: ignore[arg-type]
                assert isinstance(resources, ComponentResources)
                assert isinstance(resources.manager_client, ManagerClientInfo)
                assert resources.manager_client.client_pool is mock_manager_pool
                assert resources.manager_client.endpoints == config.api.endpoint

                # Hive router should not be setup when disabled
                assert resources.hive_router_client is None

        # Hive router client pool should not be created
        mock_hive_pool_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_stage_name(self) -> None:
        """Composer should have correct stage name."""
        composer = ComponentComposer()
        assert composer.stage_name == "components"
