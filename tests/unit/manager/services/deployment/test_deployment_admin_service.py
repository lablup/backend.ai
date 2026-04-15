"""
Mock-based unit tests for DeploymentAdminService.

Tests verify the sync_model_definitions admin operation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.repositories.deployment.admin_repository import DeploymentAdminRepository
from ai.backend.manager.services.deployment.actions.sync_model_definitions import (
    SyncModelDefinitionsAction,
)
from ai.backend.manager.services.deployment.admin_service import DeploymentAdminService


class TestDeploymentAdminService:
    """Tests for DeploymentAdminService.sync_model_definitions."""

    @pytest.fixture
    def mock_admin_repository(self) -> MagicMock:
        return MagicMock(spec=DeploymentAdminRepository)

    @pytest.fixture
    def admin_service(self, mock_admin_repository: MagicMock) -> DeploymentAdminService:
        return DeploymentAdminService(repository=mock_admin_repository)

    async def test_sync_returns_updated_and_failed_counts(
        self,
        admin_service: DeploymentAdminService,
        mock_admin_repository: MagicMock,
    ) -> None:
        mock_admin_repository.sync_model_definitions = AsyncMock(return_value=(3, 1))

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert result.updated == 3
        assert result.failed == 1
        mock_admin_repository.sync_model_definitions.assert_awaited_once()

    async def test_sync_with_no_revisions_to_update(
        self,
        admin_service: DeploymentAdminService,
        mock_admin_repository: MagicMock,
    ) -> None:
        mock_admin_repository.sync_model_definitions = AsyncMock(return_value=(0, 0))

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert result.updated == 0
        assert result.failed == 0

    async def test_sync_with_all_failures(
        self,
        admin_service: DeploymentAdminService,
        mock_admin_repository: MagicMock,
    ) -> None:
        mock_admin_repository.sync_model_definitions = AsyncMock(return_value=(0, 5))

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert result.updated == 0
        assert result.failed == 5
