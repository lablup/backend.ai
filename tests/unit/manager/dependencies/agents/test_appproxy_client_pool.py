from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.dependencies.agents.appproxy_client_pool import (
    AppProxyClientPoolDependency,
)


class TestAppProxyClientPoolDependency:
    """Test AppProxyClientPoolDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.agents.appproxy_client_pool.AppProxyClientPool")
    async def test_provide_appproxy_client_pool(
        self,
        mock_pool_class: MagicMock,
    ) -> None:
        """Dependency should create app proxy client pool and close on cleanup."""
        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_pool_class.return_value = mock_pool

        dependency = AppProxyClientPoolDependency()
        async with dependency.provide(None) as pool:
            assert pool is mock_pool
            mock_pool_class.assert_called_once()
            mock_pool.close.assert_not_called()

        mock_pool.close.assert_awaited_once()
