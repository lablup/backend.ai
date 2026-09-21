from __future__ import annotations

from unittest.mock import MagicMock, patch

from ai.backend.manager.dependencies.agents.registry_quota_client_pool import (
    RegistryQuotaClientPoolDependency,
)


class TestRegistryQuotaClientPoolDependency:
    """Test RegistryQuotaClientPoolDependency lifecycle."""

    @patch(
        "ai.backend.manager.dependencies.agents.registry_quota_client_pool"
        ".ContainerRegistryQuotaClientPool"
    )
    async def test_provide_registry_quota_client_pool(
        self,
        mock_pool_class: MagicMock,
    ) -> None:
        """Dependency should create the registry quota client pool."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        dependency = RegistryQuotaClientPoolDependency()
        async with dependency.provide(None) as pool:
            assert pool is mock_pool
            mock_pool_class.assert_called_once()
