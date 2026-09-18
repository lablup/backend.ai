from __future__ import annotations

from unittest.mock import MagicMock, patch

from ai.backend.manager.dependencies.domain.registry_quota import (
    RegistryQuotaServiceDependency,
    RegistryQuotaServiceInput,
)


class TestRegistryQuotaServiceDependency:
    """Test RegistryQuotaServiceDependency lifecycle."""

    @patch(
        "ai.backend.manager.dependencies.domain.registry_quota.PerProjectContainerRegistryQuotaClientPool"
    )
    @patch(
        "ai.backend.manager.dependencies.domain.registry_quota.PerProjectContainerRegistryQuotaService"
    )
    @patch(
        "ai.backend.manager.dependencies.domain.registry_quota.PerProjectRegistryQuotaRepository"
    )
    async def test_provide_registry_quota_service(
        self,
        mock_repo_class: MagicMock,
        mock_service_class: MagicMock,
        mock_pool_class: MagicMock,
    ) -> None:
        """Dependency should build the quota service from the repository and client pool."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        db = MagicMock()
        dependency = RegistryQuotaServiceDependency()
        setup_input = RegistryQuotaServiceInput(db=db)

        async with dependency.provide(setup_input) as service:
            assert service is mock_service
            mock_repo_class.assert_called_once_with(db)
            mock_pool_class.assert_called_once()
            mock_service_class.assert_called_once_with(
                repository=mock_repo,
                client_pool=mock_pool,
            )

    def test_stage_name(self) -> None:
        """Dependency should have correct stage name."""
        dependency = RegistryQuotaServiceDependency()
        assert dependency.stage_name == "registry-quota-service"
