"""
Mock-based unit tests for DeploymentAdminService.

Tests verify the sync_model_definitions admin operation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.deployment.types import RevisionSyncResult
from ai.backend.manager.repositories.deployment.admin_repository import DeploymentAdminRepository
from ai.backend.manager.services.deployment.actions.sync_model_definitions import (
    SyncModelDefinitionsAction,
)
from ai.backend.manager.services.deployment.admin_service import DeploymentAdminService


@dataclass
class SyncTestCase:
    repo_result: list[RevisionSyncResult]
    expected_count: int
    expected_all_success: bool


class TestDeploymentAdminService:
    """Tests for DeploymentAdminService.sync_model_definitions."""

    @pytest.fixture
    def mock_admin_repository(self) -> MagicMock:
        return MagicMock(spec=DeploymentAdminRepository)

    @pytest.fixture
    def admin_service(self, mock_admin_repository: MagicMock) -> DeploymentAdminService:
        return DeploymentAdminService(repository=mock_admin_repository)

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                SyncTestCase(repo_result=[], expected_count=0, expected_all_success=True),
                id="no-revisions",
            ),
            pytest.param(
                SyncTestCase(
                    repo_result=[RevisionSyncResult(revision_id=uuid.uuid4(), success=True)],
                    expected_count=1,
                    expected_all_success=True,
                ),
                id="single-success",
            ),
            pytest.param(
                SyncTestCase(
                    repo_result=[
                        RevisionSyncResult(
                            revision_id=uuid.uuid4(),
                            success=False,
                            failure_reason="error",
                        )
                    ],
                    expected_count=1,
                    expected_all_success=False,
                ),
                id="single-failure",
            ),
            pytest.param(
                SyncTestCase(
                    repo_result=[
                        RevisionSyncResult(revision_id=uuid.uuid4(), success=True),
                        RevisionSyncResult(
                            revision_id=uuid.uuid4(),
                            success=False,
                            failure_reason="file not found",
                        ),
                        RevisionSyncResult(revision_id=uuid.uuid4(), success=True),
                    ],
                    expected_count=3,
                    expected_all_success=False,
                ),
                id="mixed-results",
            ),
        ],
    )
    async def test_sync_delegates_to_repository_and_returns_results(
        self,
        admin_service: DeploymentAdminService,
        mock_admin_repository: MagicMock,
        case: SyncTestCase,
    ) -> None:
        mock_admin_repository.sync_model_definitions = AsyncMock(return_value=case.repo_result)

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert len(result.results) == case.expected_count
        assert all(r.success for r in result.results) == case.expected_all_success
        mock_admin_repository.sync_model_definitions.assert_awaited_once()
