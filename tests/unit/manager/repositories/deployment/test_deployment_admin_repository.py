"""
Mock-based unit tests for DeploymentAdminRepository.

Tests verify the sync_model_definitions operation using mocked db_source and storage_source.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.config import ModelDefinition
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.data.deployment.types import RevisionWithVFolderInfo
from ai.backend.manager.data.vfolder.types import VFolderOwnershipType
from ai.backend.manager.repositories.deployment.admin_repository import DeploymentAdminRepository
from ai.backend.manager.repositories.deployment.db_source import DeploymentDBSource
from ai.backend.manager.repositories.deployment.storage_source import DeploymentStorageSource


class TestDeploymentAdminRepository:
    """Tests for DeploymentAdminRepository.sync_model_definitions."""

    @pytest.fixture
    def mock_db_source(self) -> AsyncMock:
        return AsyncMock(spec=DeploymentDBSource)

    @pytest.fixture
    def mock_storage_source(self) -> AsyncMock:
        return AsyncMock(spec=DeploymentStorageSource)

    @pytest.fixture
    def admin_repository(
        self, mock_db_source: AsyncMock, mock_storage_source: AsyncMock
    ) -> DeploymentAdminRepository:
        return DeploymentAdminRepository(
            db_source=mock_db_source, storage_source=mock_storage_source
        )

    def _make_revision_info(
        self,
        *,
        revision_id: uuid.UUID | None = None,
        vfolder_id: uuid.UUID | None = None,
        model_definition_path: str | None = "model-definition.yaml",
        model_definition: dict[str, Any] | None = None,
    ) -> RevisionWithVFolderInfo:
        rid = revision_id or uuid.uuid4()
        vid = vfolder_id or uuid.uuid4()
        return RevisionWithVFolderInfo(
            revision_id=rid,
            model_definition=model_definition,
            model_definition_path=model_definition_path,
            vfolder_id=vid,
            vfolder_quota_scope_id=uuid.uuid4(),
            vfolder_host="local:volume1",
            vfolder_ownership_type=VFolderOwnershipType.USER,
            vfolder_usage_mode=VFolderUsageMode.MODEL,
        )

    async def test_sync_no_revisions(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_db_source: AsyncMock,
    ) -> None:
        mock_db_source.get_revisions_with_vfolder_info.return_value = []

        results = await admin_repository.sync_model_definitions()

        assert results == []

    async def test_sync_successful_update(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_db_source: AsyncMock,
        mock_storage_source: AsyncMock,
    ) -> None:
        rev_id = uuid.uuid4()
        row = self._make_revision_info(revision_id=rev_id)
        yaml_content = b"models:\n  - name: test\n    model_path: /models\n"

        mock_db_source.get_revisions_with_vfolder_info.return_value = [row]
        mock_storage_source.fetch_definition_file.return_value = yaml_content

        results = await admin_repository.sync_model_definitions()

        assert len(results) == 1
        assert results[0].revision_id == rev_id
        assert results[0].success is True
        mock_db_source.batch_update_model_definitions.assert_awaited_once()

    async def test_sync_fetch_failure_returns_error_with_reason(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_db_source: AsyncMock,
        mock_storage_source: AsyncMock,
    ) -> None:
        rev_id = uuid.uuid4()
        row = self._make_revision_info(revision_id=rev_id)

        mock_db_source.get_revisions_with_vfolder_info.return_value = [row]
        mock_storage_source.fetch_definition_file.side_effect = Exception("storage unreachable")

        results = await admin_repository.sync_model_definitions()

        assert len(results) == 1
        assert results[0].revision_id == rev_id
        assert results[0].success is False
        assert "storage unreachable" in results[0].reason

    async def test_sync_mixed_success_and_failure(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_db_source: AsyncMock,
        mock_storage_source: AsyncMock,
    ) -> None:
        rev_ok = uuid.uuid4()
        rev_fail = uuid.uuid4()
        row_ok = self._make_revision_info(revision_id=rev_ok)
        row_fail = self._make_revision_info(revision_id=rev_fail)
        yaml_content = b"models:\n  - name: test\n    model_path: /models\n"

        mock_db_source.get_revisions_with_vfolder_info.return_value = [row_ok, row_fail]

        call_count = 0

        async def fetch_side_effect(*args: Any, **kwargs: Any) -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return yaml_content
            raise Exception("file not found")

        mock_storage_source.fetch_definition_file.side_effect = fetch_side_effect

        results = await admin_repository.sync_model_definitions()

        succeeded = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        assert len(succeeded) == 1
        assert succeeded[0].revision_id == rev_ok
        assert len(failed) == 1
        assert failed[0].revision_id == rev_fail

    async def test_sync_skips_when_already_in_sync(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_db_source: AsyncMock,
        mock_storage_source: AsyncMock,
    ) -> None:
        yaml_content = b"models:\n  - name: test\n    model_path: /models\n"
        existing_def = ModelDefinition.model_validate({
            "models": [{"name": "test", "model_path": "/models"}]
        }).model_dump(exclude_none=True, by_alias=True)
        row = self._make_revision_info(model_definition=existing_def)

        mock_db_source.get_revisions_with_vfolder_info.return_value = [row]
        mock_storage_source.fetch_definition_file.return_value = yaml_content

        results = await admin_repository.sync_model_definitions()

        assert results == []
        mock_db_source.batch_update_model_definitions.assert_not_awaited()

    async def test_sync_updates_when_content_differs(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_db_source: AsyncMock,
        mock_storage_source: AsyncMock,
    ) -> None:
        rev_id = uuid.uuid4()
        old_def: dict[str, Any] = {"models": [{"name": "old-model", "model_path": "/models"}]}
        row = self._make_revision_info(revision_id=rev_id, model_definition=old_def)
        yaml_content = b"models:\n  - name: new-model\n    model_path: /models\n"

        mock_db_source.get_revisions_with_vfolder_info.return_value = [row]
        mock_storage_source.fetch_definition_file.return_value = yaml_content

        results = await admin_repository.sync_model_definitions()

        assert len(results) == 1
        assert results[0].revision_id == rev_id
        assert results[0].success is True
