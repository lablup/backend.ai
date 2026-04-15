"""
Mock-based unit tests for DeploymentAdminRepository.

Tests verify the sync_model_definitions operation using mocked DB and storage.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.data.vfolder.types import VFolderOwnershipType
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.deployment.admin_repository import DeploymentAdminRepository


class TestDeploymentAdminRepository:
    """Tests for DeploymentAdminRepository.sync_model_definitions."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        return MagicMock(spec=ExtendedAsyncSAEngine)

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        return MagicMock(spec=StorageSessionManager)

    @pytest.fixture
    def admin_repository(
        self, mock_db: MagicMock, mock_storage_manager: MagicMock
    ) -> DeploymentAdminRepository:
        return DeploymentAdminRepository(db=mock_db, storage_manager=mock_storage_manager)

    def _make_revision_row(
        self,
        *,
        revision_id: uuid.UUID | None = None,
        vfolder_id: uuid.UUID | None = None,
        model_definition_path: str | None = "model-definition.yaml",
    ) -> MagicMock:
        row = MagicMock()
        row.id = revision_id or uuid.uuid4()
        row.model = vfolder_id or uuid.uuid4()
        row.model_definition_path = model_definition_path
        row.vf_id = vfolder_id or row.model
        row.vf_quota_scope_id = uuid.uuid4()
        row.vf_host = "local:volume1"
        row.vf_ownership_type = VFolderOwnershipType.USER
        row.vf_usage_mode = VFolderUsageMode.MODEL
        return row

    async def test_sync_no_revisions(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_db: MagicMock,
    ) -> None:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.begin_readonly_session = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session))
        )

        updated, failed = await admin_repository.sync_model_definitions()

        assert updated == 0
        assert failed == 0

    async def test_sync_successful_update(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_db: MagicMock,
    ) -> None:
        row = self._make_revision_row()
        yaml_content = b"models:\n  - name: test\n    model_path: /models\n"

        # Mock readonly session for query
        mock_readonly_session = AsyncMock()
        mock_query_result = MagicMock()
        mock_query_result.all.return_value = [row]
        mock_readonly_session.execute = AsyncMock(return_value=mock_query_result)

        # Mock write session for update
        mock_write_session = AsyncMock()

        mock_db.begin_readonly_session = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_readonly_session))
        )
        mock_db.begin_session = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_write_session))
        )

        with patch(
            "ai.backend.manager.repositories.deployment.admin_repository.DeploymentStorageSource"
        ) as mock_storage_cls:
            mock_storage = AsyncMock()
            mock_storage.fetch_definition_file = AsyncMock(return_value=yaml_content)
            mock_storage_cls.return_value = mock_storage

            updated, failed = await admin_repository.sync_model_definitions()

        assert updated == 1
        assert failed == 0
        mock_write_session.execute.assert_awaited_once()

    async def test_sync_fetch_failure_skips_revision(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_db: MagicMock,
    ) -> None:
        row = self._make_revision_row()

        mock_readonly_session = AsyncMock()
        mock_query_result = MagicMock()
        mock_query_result.all.return_value = [row]
        mock_readonly_session.execute = AsyncMock(return_value=mock_query_result)

        mock_db.begin_readonly_session = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_readonly_session))
        )

        with patch(
            "ai.backend.manager.repositories.deployment.admin_repository.DeploymentStorageSource"
        ) as mock_storage_cls:
            mock_storage = AsyncMock()
            mock_storage.fetch_definition_file = AsyncMock(
                side_effect=Exception("storage unreachable")
            )
            mock_storage_cls.return_value = mock_storage

            updated, failed = await admin_repository.sync_model_definitions()

        assert updated == 0
        assert failed == 1

    async def test_sync_mixed_success_and_failure(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_db: MagicMock,
    ) -> None:
        row_ok = self._make_revision_row()
        row_fail = self._make_revision_row()
        yaml_content = b"models:\n  - name: test\n    model_path: /models\n"

        mock_readonly_session = AsyncMock()
        mock_query_result = MagicMock()
        mock_query_result.all.return_value = [row_ok, row_fail]
        mock_readonly_session.execute = AsyncMock(return_value=mock_query_result)

        mock_write_session = AsyncMock()

        mock_db.begin_readonly_session = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_readonly_session))
        )
        mock_db.begin_session = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_write_session))
        )

        call_count = 0

        async def fetch_side_effect(*args: Any, **kwargs: Any) -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return yaml_content
            raise Exception("file not found")

        with patch(
            "ai.backend.manager.repositories.deployment.admin_repository.DeploymentStorageSource"
        ) as mock_storage_cls:
            mock_storage = AsyncMock()
            mock_storage.fetch_definition_file = AsyncMock(side_effect=fetch_side_effect)
            mock_storage_cls.return_value = mock_storage

            updated, failed = await admin_repository.sync_model_definitions()

        assert updated == 1
        assert failed == 1
