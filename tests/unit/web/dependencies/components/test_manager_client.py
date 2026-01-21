from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.typed_validators import CommaSeparatedStrList
from ai.backend.web.dependencies.components.manager_client import (
    ManagerClientInfo,
    ManagerClientProvider,
)


@dataclass
class MockAPIConfig:
    """Mock for API configuration."""

    endpoint: CommaSeparatedStrList
    ssl_verify: bool
    connection_limit: int


@dataclass
class MockConfig:
    """Mock for web server config."""

    api: MockAPIConfig


class TestManagerClientProvider:
    """Test ManagerClientProvider lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.web.dependencies.components.manager_client.ClientPool")
    async def test_provide_manager_client(self, mock_client_pool_class: MagicMock) -> None:
        """Provider should create and close manager client pool."""
        config = MockConfig(
            api=MockAPIConfig(
                endpoint=CommaSeparatedStrList("http://127.0.0.1:8081,http://127.0.0.1:8082"),
                ssl_verify=True,
                connection_limit=100,
            )
        )

        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_client_pool_class.return_value = mock_pool

        provider = ManagerClientProvider()

        async with provider.provide(config) as client_info:  # type: ignore[arg-type]
            assert isinstance(client_info, ManagerClientInfo)
            assert client_info.client_pool is mock_pool
            # CommaSeparatedStrList is a list subclass
            assert client_info.endpoints == config.api.endpoint
            mock_client_pool_class.assert_called_once()

        # Client pool should be closed after context exit
        mock_pool.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.web.dependencies.components.manager_client.ClientPool")
    async def test_cleanup_on_exception(self, mock_client_pool_class: MagicMock) -> None:
        """Provider should cleanup client pool even on exception."""
        config = MockConfig(
            api=MockAPIConfig(
                endpoint=CommaSeparatedStrList("http://127.0.0.1:8081"),
                ssl_verify=False,
                connection_limit=50,
            )
        )

        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_client_pool_class.return_value = mock_pool

        provider = ManagerClientProvider()

        with pytest.raises(RuntimeError):
            async with provider.provide(config) as client_info:  # type: ignore[arg-type]
                assert isinstance(client_info, ManagerClientInfo)
                raise RuntimeError("Test error")

        # Client pool should still be closed
        mock_pool.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.web.dependencies.components.manager_client.ClientPool")
    async def test_stage_name(self, mock_client_pool_class: MagicMock) -> None:
        """Provider should have correct stage name."""
        provider = ManagerClientProvider()
        assert provider.stage_name == "manager-client"
