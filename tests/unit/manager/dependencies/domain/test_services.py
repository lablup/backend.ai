from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.domain.services import (
    ServicesContextDependency,
    ServicesInput,
)


class TestServicesContextDependency:
    """Test ServicesContextDependency lifecycle."""

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.domain.services.PerProjectContainerRegistryQuotaClientPool"
    )
    @patch(
        "ai.backend.manager.dependencies.domain.services.PerProjectContainerRegistryQuotaService"
    )
    @patch("ai.backend.manager.dependencies.domain.services.PerProjectRegistryQuotaRepository")
    async def test_provide_services_context(
        self,
        mock_repo_class: MagicMock,
        mock_service_class: MagicMock,
        mock_pool_class: MagicMock,
    ) -> None:
        """Dependency should create ServicesContext with correct services."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        db = MagicMock()
        dependency = ServicesContextDependency()
        services_input = ServicesInput(db=db)

        async with dependency.provide(services_input) as svc_ctx:
            assert svc_ctx.per_project_container_registries_quota is mock_service
            mock_repo_class.assert_called_once_with(db)
            mock_pool_class.assert_called_once()
            mock_service_class.assert_called_once_with(
                repository=mock_repo,
                client_pool=mock_pool,
            )

    def test_stage_name(self) -> None:
        """Dependency should have correct stage name."""
        dependency = ServicesContextDependency()
        assert dependency.stage_name == "services-context"
