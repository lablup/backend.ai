"""
Mock-based unit tests for DeploymentAdminService.

Tests verify the sync_model_definitions admin operation.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.repositories.deployment.admin_repository import DeploymentAdminRepository
from ai.backend.manager.services.deployment.actions.sync_model_definitions import (
    RevisionSyncStatus,
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

    async def test_sync_returns_per_revision_results(
        self,
        admin_service: DeploymentAdminService,
        mock_admin_repository: MagicMock,
    ) -> None:
        rev1, rev2 = uuid.uuid4(), uuid.uuid4()
        mock_admin_repository.sync_model_definitions = AsyncMock(
            return_value=[
                RevisionSyncStatus(revision_id=rev1, success=True),
                RevisionSyncStatus(revision_id=rev2, success=False, reason="file not found"),
            ]
        )

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert len(result.results) == 2
        assert result.results[0].revision_id == rev1
        assert result.results[0].success is True
        assert result.results[1].revision_id == rev2
        assert result.results[1].success is False
        assert result.results[1].reason == "file not found"

    async def test_sync_with_no_revisions(
        self,
        admin_service: DeploymentAdminService,
        mock_admin_repository: MagicMock,
    ) -> None:
        mock_admin_repository.sync_model_definitions = AsyncMock(return_value=[])

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert result.results == []

    async def test_sync_with_all_failures(
        self,
        admin_service: DeploymentAdminService,
        mock_admin_repository: MagicMock,
    ) -> None:
        revisions = [uuid.uuid4() for _ in range(3)]
        mock_admin_repository.sync_model_definitions = AsyncMock(
            return_value=[
                RevisionSyncStatus(revision_id=r, success=False, reason="error") for r in revisions
            ]
        )

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert len(result.results) == 3
        assert all(not r.success for r in result.results)
