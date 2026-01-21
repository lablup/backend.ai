from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.typed_validators import CommaSeparatedStrList
from ai.backend.web.dependencies.components.hive_router_client import (
    HiveRouterClientInfo,
    HiveRouterClientProvider,
)


@dataclass
class MockApolloRouterConfig:
    """Mock for Apollo Router configuration."""

    enabled: bool
    endpoints: CommaSeparatedStrList


@dataclass
class MockConfig:
    """Mock for web server config."""

    apollo_router: MockApolloRouterConfig


class TestHiveRouterClientProvider:
    """Test HiveRouterClientProvider lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.web.dependencies.components.hive_router_client.ClientPool")
    async def test_provide_hive_router_client(self, mock_client_pool_class: MagicMock) -> None:
        """Provider should create and close hive router client pool."""
        config = MockConfig(
            apollo_router=MockApolloRouterConfig(
                enabled=True,
                endpoints=CommaSeparatedStrList("http://router1:4000,http://router2:4000"),
            )
        )

        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_client_pool_class.return_value = mock_pool

        provider = HiveRouterClientProvider()

        async with provider.provide(config) as client_info:  # type: ignore[arg-type]
            assert isinstance(client_info, HiveRouterClientInfo)
            assert client_info.client_pool is mock_pool
            # CommaSeparatedStrList is a list subclass
            assert client_info.endpoints == config.apollo_router.endpoints
            mock_client_pool_class.assert_called_once()

        # Client pool should be closed after context exit
        mock_pool.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.web.dependencies.components.hive_router_client.ClientPool")
    async def test_cleanup_on_exception(self, mock_client_pool_class: MagicMock) -> None:
        """Provider should cleanup client pool even on exception."""
        config = MockConfig(
            apollo_router=MockApolloRouterConfig(
                enabled=True,
                endpoints=CommaSeparatedStrList("http://router:4000"),
            )
        )

        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_client_pool_class.return_value = mock_pool

        provider = HiveRouterClientProvider()

        with pytest.raises(RuntimeError):
            async with provider.provide(config) as client_info:  # type: ignore[arg-type]
                assert isinstance(client_info, HiveRouterClientInfo)
                raise RuntimeError("Test error")

        # Client pool should still be closed
        mock_pool.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.web.dependencies.components.hive_router_client.ClientPool")
    async def test_stage_name(self, mock_client_pool_class: MagicMock) -> None:
        """Provider should have correct stage name."""
        provider = HiveRouterClientProvider()
        assert provider.stage_name == "hive-router-client"
