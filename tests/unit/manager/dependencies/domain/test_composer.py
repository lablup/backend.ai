from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.dependencies import DependencyBuilderStack
from ai.backend.manager.dependencies.domain.composer import (
    DomainComposer,
    DomainInput,
)


class TestDomainComposer:
    """Test DomainComposer integration."""

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.domain.services.PerProjectContainerRegistryQuotaClientPool"
    )
    @patch(
        "ai.backend.manager.dependencies.domain.services.PerProjectContainerRegistryQuotaService"
    )
    @patch("ai.backend.manager.dependencies.domain.services.PerProjectRegistryQuotaRepository")
    @patch("ai.backend.manager.dependencies.domain.repositories.Repositories")
    @patch("ai.backend.manager.dependencies.domain.distributed_lock.create_lock_factory")
    @patch("ai.backend.manager.dependencies.domain.notification.NotificationCenter")
    async def test_compose_all_dependencies(
        self,
        mock_nc_class: MagicMock,
        mock_create_lock: MagicMock,
        mock_repos_class: MagicMock,
        mock_quota_repo_class: MagicMock,
        mock_quota_service_class: MagicMock,
        mock_quota_pool_class: MagicMock,
    ) -> None:
        """DomainComposer should initialize all four domain dependencies."""
        # Setup mocks
        mock_nc = MagicMock()
        mock_nc.close = AsyncMock()
        mock_nc_class.return_value = mock_nc

        mock_factory = MagicMock()
        mock_create_lock.return_value = mock_factory

        mock_repos = MagicMock()
        mock_repos_class.create.return_value = mock_repos

        mock_quota_service_class.return_value = MagicMock()

        domain_input = DomainInput(
            config_provider=MagicMock(),
            db=MagicMock(),
            etcd=MagicMock(),
            storage_manager=MagicMock(),
            valkey_stat=MagicMock(),
            valkey_live=MagicMock(),
            valkey_schedule=MagicMock(),
            valkey_image=MagicMock(),
        )

        composer = DomainComposer()
        async with DependencyBuilderStack() as stack:
            resources = await stack.enter_composer(composer, domain_input)

            assert resources.notification_center is mock_nc
            assert resources.distributed_lock_factory is mock_factory
            assert resources.repositories is mock_repos
            assert resources.services_ctx is not None

        # Cleanup should have been called
        mock_nc.close.assert_called_once()

    def test_stage_name(self) -> None:
        """DomainComposer should have correct stage name."""
        composer = DomainComposer()
        assert composer.stage_name == "domain"
