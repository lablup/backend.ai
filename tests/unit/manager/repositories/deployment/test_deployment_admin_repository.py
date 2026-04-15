"""
Real-DB unit tests for DeploymentAdminRepository.sync_model_definitions.

Uses a real database via `with_tables` to verify that the repository correctly
reads revisions joined with vfolder info and writes updated model_definition
values. DeploymentStorageSource is mocked because it is an HTTP boundary to
the storage proxy, not a database concern.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.config import ModelDefinition
from ai.backend.common.types import ClusterMode, QuotaScopeID, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.resource_slot.row import (
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.deployment.admin_repository import DeploymentAdminRepository
from ai.backend.manager.repositories.deployment.db_source import DeploymentDBSource
from ai.backend.manager.repositories.deployment.storage_source import DeploymentStorageSource
from ai.backend.testutils.db import with_tables

YAML_CONTENT = b"models:\n  - name: test\n    model_path: /models\n"
YAML_EXPECTED_STORED = ModelDefinition.model_validate({
    "models": [{"name": "test", "model_path": "/models"}]
}).model_dump(exclude_none=True, by_alias=True)


class TestDeploymentAdminRepositorySyncModelDefinitions:
    """Tests for DeploymentAdminRepository.sync_model_definitions against a real DB."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                ResourceSlotTypeRow,
                VFolderRow,
                DeploymentRevisionRow,
                DeploymentRevisionResourceSlotRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def mock_storage_source(self) -> AsyncMock:
        return AsyncMock(spec=DeploymentStorageSource)

    @pytest.fixture
    def admin_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> DeploymentAdminRepository:
        db_source = DeploymentDBSource(db=db_with_cleanup, storage_manager=MagicMock())
        return DeploymentAdminRepository(db_source=db_source, storage_source=mock_storage_source)

    async def _insert_revision(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        model_definition: dict[str, Any] | None,
        endpoint_id: uuid.UUID | None = None,
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """Insert a VFolder + DeploymentRevision pair. Returns (revision_id, vfolder_id)."""
        vfolder_id = uuid.uuid4()
        revision_id = uuid.uuid4()
        user_id = uuid.uuid4()

        async with db.begin_session() as db_sess:
            db_sess.add(
                VFolderRow(
                    id=vfolder_id,
                    name=f"model-{vfolder_id.hex[:8]}",
                    host="local:volume1",
                    domain_name="default",
                    quota_scope_id=QuotaScopeID.parse(f"user:{user_id}"),
                    usage_mode=VFolderUsageMode.MODEL,
                    permission=VFolderMountPermission.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    creator="test@example.com",
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.USER,
                    user=user_id,
                    group=None,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
            db_sess.add(
                DeploymentRevisionRow(
                    id=revision_id,
                    endpoint=endpoint_id or uuid.uuid4(),
                    revision_number=1,
                    image=uuid.uuid4(),
                    model=vfolder_id,
                    model_mount_destination="/models",
                    model_definition_path="model-definition.yaml",
                    model_definition=model_definition,
                    resource_group="default",
                    resource_opts={},
                    cluster_mode=ClusterMode.SINGLE_NODE.name,
                    cluster_size=1,
                    runtime_variant="custom",
                    environ={},
                    extra_mounts=[],
                )
            )
            await db_sess.commit()
        return revision_id, vfolder_id

    async def _fetch_model_definition(
        self,
        db: ExtendedAsyncSAEngine,
        revision_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        async with db.begin_readonly_session() as db_sess:
            result = await db_sess.execute(
                sa.select(DeploymentRevisionRow.model_definition).where(
                    DeploymentRevisionRow.id == revision_id
                )
            )
            stored: dict[str, Any] | None = result.scalar_one()
            return stored

    async def test_sync_no_revisions(
        self,
        admin_repository: DeploymentAdminRepository,
        mock_storage_source: AsyncMock,
    ) -> None:
        results = await admin_repository.sync_model_definitions()

        assert results == []
        mock_storage_source.fetch_definition_file.assert_not_called()

    async def test_sync_populates_null_model_definition(
        self,
        admin_repository: DeploymentAdminRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> None:
        revision_id, _ = await self._insert_revision(db_with_cleanup, model_definition=None)
        mock_storage_source.fetch_definition_file.return_value = YAML_CONTENT

        results = await admin_repository.sync_model_definitions()

        assert len(results) == 1
        assert results[0].revision_id == revision_id
        assert results[0].success is True
        stored = await self._fetch_model_definition(db_with_cleanup, revision_id)
        assert stored == YAML_EXPECTED_STORED

    async def test_sync_skips_when_already_in_sync(
        self,
        admin_repository: DeploymentAdminRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> None:
        revision_id, _ = await self._insert_revision(
            db_with_cleanup, model_definition=YAML_EXPECTED_STORED
        )
        mock_storage_source.fetch_definition_file.return_value = YAML_CONTENT

        results = await admin_repository.sync_model_definitions()

        assert results == []
        stored = await self._fetch_model_definition(db_with_cleanup, revision_id)
        assert stored == YAML_EXPECTED_STORED

    async def test_sync_updates_when_content_differs(
        self,
        admin_repository: DeploymentAdminRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> None:
        outdated = {"models": [{"name": "old-model", "model_path": "/models"}]}
        revision_id, _ = await self._insert_revision(db_with_cleanup, model_definition=outdated)
        mock_storage_source.fetch_definition_file.return_value = YAML_CONTENT

        results = await admin_repository.sync_model_definitions()

        assert len(results) == 1
        assert results[0].revision_id == revision_id
        assert results[0].success is True
        stored = await self._fetch_model_definition(db_with_cleanup, revision_id)
        assert stored == YAML_EXPECTED_STORED

    async def test_sync_reports_fetch_failure_and_leaves_db_untouched(
        self,
        admin_repository: DeploymentAdminRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> None:
        revision_id, _ = await self._insert_revision(db_with_cleanup, model_definition=None)
        mock_storage_source.fetch_definition_file.side_effect = Exception("storage unreachable")

        results = await admin_repository.sync_model_definitions()

        assert len(results) == 1
        assert results[0].revision_id == revision_id
        assert results[0].success is False
        assert results[0].failure_reason is not None
        assert "storage unreachable" in results[0].failure_reason
        stored = await self._fetch_model_definition(db_with_cleanup, revision_id)
        assert stored is None

    async def test_sync_mixed_success_and_failure_across_revisions(
        self,
        admin_repository: DeploymentAdminRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> None:
        rev_ok, _ = await self._insert_revision(db_with_cleanup, model_definition=None)
        rev_fail, _ = await self._insert_revision(db_with_cleanup, model_definition=None)

        call_count = 0

        async def fetch_side_effect(*args: Any, **kwargs: Any) -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return YAML_CONTENT
            raise Exception("file not found")

        mock_storage_source.fetch_definition_file.side_effect = fetch_side_effect

        results = await admin_repository.sync_model_definitions()

        by_id = {r.revision_id: r for r in results}
        assert by_id[rev_ok].success is True
        assert by_id[rev_fail].success is False
        fail_reason = by_id[rev_fail].failure_reason
        assert fail_reason is not None
        assert "file not found" in fail_reason

        stored_ok = await self._fetch_model_definition(db_with_cleanup, rev_ok)
        stored_fail = await self._fetch_model_definition(db_with_cleanup, rev_fail)
        assert stored_ok == YAML_EXPECTED_STORED
        assert stored_fail is None

    async def test_sync_ignores_revisions_without_model_vfolder(
        self,
        admin_repository: DeploymentAdminRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> None:
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DeploymentRevisionRow(
                    id=uuid.uuid4(),
                    endpoint=uuid.uuid4(),
                    revision_number=1,
                    image=uuid.uuid4(),
                    model=None,
                    model_mount_destination="/models",
                    model_definition=None,
                    resource_group="default",
                    resource_opts={},
                    cluster_mode=ClusterMode.SINGLE_NODE.name,
                    cluster_size=1,
                    runtime_variant="custom",
                    environ={},
                    extra_mounts=[],
                )
            )
            await db_sess.commit()

        results = await admin_repository.sync_model_definitions()

        assert results == []
        mock_storage_source.fetch_definition_file.assert_not_called()
