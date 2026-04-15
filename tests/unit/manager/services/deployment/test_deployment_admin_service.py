"""
Real-DB unit tests for DeploymentAdminService.sync_model_definitions.

Exercises the full service -> repository -> DB chain with a real Postgres via
with_tables. DeploymentStorageSource is mocked because it is an HTTP boundary
to the storage proxy, not a database concern.

Overrides the parent services/conftest.py guard on `database_connection` to
opt this file into real-DB testing.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.config import ModelDefinition
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ClusterMode, QuotaScopeID, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.deployment import DefinitionFileNotFound
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.resource_slot.row import (
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, create_async_engine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.deployment.admin_repository import DeploymentAdminRepository
from ai.backend.manager.repositories.deployment.db_source import DeploymentDBSource
from ai.backend.manager.repositories.deployment.storage_source import DeploymentStorageSource
from ai.backend.manager.services.deployment.actions.sync_model_definitions import (
    SyncModelDefinitionsAction,
)
from ai.backend.manager.services.deployment.admin_service import DeploymentAdminService
from ai.backend.testutils.bootstrap import postgres_container  # noqa: F401
from ai.backend.testutils.db import with_tables

_YAML_CONTENT = b"models:\n  - name: test\n    model_path: /models\n"
_YAML_EXPECTED_STORED = ModelDefinition.model_validate({
    "models": [{"name": "test", "model_path": "/models"}]
}).model_dump(exclude_none=True, by_alias=True)


@pytest.fixture
async def database_connection(
    postgres_container: tuple[str, HostPortPairModel],  # noqa: F811
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    """
    Local override for the parent services/conftest.py guard.

    This test exercises the service through the real repository, so it needs a
    real database connection. Other service tests continue to hit the guard.
    """
    _, addr = postgres_container
    url = f"postgresql+asyncpg://postgres:develove@{addr.host}:{addr.port}/testing"
    engine = create_async_engine(
        url,
        pool_size=8,
        pool_pre_ping=False,
        max_overflow=64,
    )
    yield engine
    await engine.dispose()


class TestDeploymentAdminServiceSyncModelDefinitions:
    """Tests for DeploymentAdminService.sync_model_definitions against a real DB."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
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
    def admin_service(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> DeploymentAdminService:
        db_source = DeploymentDBSource(db=db_with_cleanup, storage_manager=MagicMock())
        repository = DeploymentAdminRepository(
            db_source=db_source, storage_source=mock_storage_source
        )
        return DeploymentAdminService(repository=repository)

    async def _insert_revision(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        model_definition: dict[str, Any] | None,
    ) -> uuid.UUID:
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
                    endpoint=uuid.uuid4(),
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
        return revision_id

    async def test_sync_returns_empty_result_when_no_revisions(
        self,
        admin_service: DeploymentAdminService,
    ) -> None:
        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert result.results == []

    async def test_sync_returns_success_entries_for_populated_revisions(
        self,
        admin_service: DeploymentAdminService,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> None:
        revision_id = await self._insert_revision(db_with_cleanup, model_definition=None)
        mock_storage_source.fetch_definition_file.return_value = _YAML_CONTENT

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert len(result.results) == 1
        assert result.results[0].revision_id == revision_id
        assert result.results[0].success is True

    async def test_sync_returns_failure_entry_with_reason(
        self,
        admin_service: DeploymentAdminService,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> None:
        revision_id = await self._insert_revision(db_with_cleanup, model_definition=None)
        mock_storage_source.fetch_definition_file.side_effect = DefinitionFileNotFound(
            "file not found"
        )

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        assert len(result.results) == 1
        assert result.results[0].revision_id == revision_id
        assert result.results[0].success is False
        fail_reason = result.results[0].failure_reason
        assert fail_reason is not None
        assert "file not found" in fail_reason

    async def test_sync_forwards_all_revisions_in_mixed_outcome(
        self,
        admin_service: DeploymentAdminService,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_source: AsyncMock,
    ) -> None:
        rev_ok = await self._insert_revision(db_with_cleanup, model_definition=None)
        rev_fail = await self._insert_revision(db_with_cleanup, model_definition=None)

        call_count = 0

        async def fetch_side_effect(*args: Any, **kwargs: Any) -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _YAML_CONTENT
            raise DefinitionFileNotFound("file not found")

        mock_storage_source.fetch_definition_file.side_effect = fetch_side_effect

        result = await admin_service.sync_model_definitions(SyncModelDefinitionsAction())

        by_id = {r.revision_id: r for r in result.results}
        assert by_id[rev_ok].success is True
        assert by_id[rev_fail].success is False
