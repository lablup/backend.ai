"""
Mock-based unit tests for DeploymentAdminService.

Tests verify the sync_model_definitions admin operation.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.deployment.types import SingleRevisionSyncResult
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

    @pytest.mark.parametrize(
        "repo_result",
        [
            pytest.param([], id="no-revisions"),
            pytest.param(
                [SingleRevisionSyncResult(revision_id=uuid.uuid4(), success=True)],
                id="single-success",
            ),
            pytest.param(
                [
                    SingleRevisionSyncResult(
                        revision_id=uuid.uuid4(),
                        success=False,
                        failure_reason="error",
                    )
                ],
                id="single-failure",
            ),
            pytest.param(
                [
                    SingleRevisionSyncResult(revision_id=uuid.uuid4(), success=True),
                    SingleRevisionSyncResult(
                        revision_id=uuid.uuid4(),
                        success=False,
                        failure_reason="file not found",
                    ),
                    SingleRevisionSyncResult(revision_id=uuid.uuid4(), success=True),
                ],
                id="mixed-results",
            ),
        ],
    )
    async def test_sync_delegates_to_repository_and_returns_results(
        self,
        admin_service: DeploymentAdminService,
        mock_admin_repository: MagicMock,
        repo_result: list[SingleRevisionSyncResult],
    ) -> None:
        mock_admin_repository.sync_model_definitions = AsyncMock(return_value=repo_result)

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert result.results == repo_result
        mock_admin_repository.sync_model_definitions.assert_awaited_once()
