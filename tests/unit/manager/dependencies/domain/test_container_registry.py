from __future__ import annotations

from unittest.mock import MagicMock, patch

from ai.backend.manager.dependencies.domain.container_registry import (
    ContainerRegistryClients,
    ContainerRegistryDependency,
)


class TestContainerRegistryDependency:
    """Test ContainerRegistryDependency lifecycle."""

    @patch(
        "ai.backend.manager.dependencies.domain.container_registry.ContainerRegistryQuotaClientPool"
    )
    async def test_provide_container_registry_clients(
        self,
        mock_pool_class: MagicMock,
    ) -> None:
        """Dependency should create the quota client pool and hand it out as the clients."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        dependency = ContainerRegistryDependency()
        async with dependency.provide(None) as clients:
            assert isinstance(clients, ContainerRegistryClients)
            assert clients.quota_pool is mock_pool
            mock_pool_class.assert_called_once()
