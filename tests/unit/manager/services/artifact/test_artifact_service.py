"""
Tests for ArtifactService functionality.
Tests the service layer with mocked repository operations.
Only artifact-related tests. Revision tests are in artifact_revision/test_artifact_revision_service.py
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from aiohttp.client_exceptions import ClientConnectorError

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelSortKey, ModelTarget
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactFilterOptions,
    ArtifactListResult,
    ArtifactRevisionData,
    ArtifactStatus,
    ArtifactType,
    ArtifactWithRevisionsListResult,
    DelegateeTarget,
)
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.errors.artifact_registry import (
    ArtifactRegistryBadScanRequestError,
    ReservoirConnectionError,
)
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact.updaters import ArtifactUpdaterSpec
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.artifact.actions.delegate_scan import (
    DelegateScanArtifactsAction,
)
from ai.backend.manager.services.artifact.actions.delete_multi import (
    DeleteArtifactsAction,
)
from ai.backend.manager.services.artifact.actions.get import (
    GetArtifactAction,
)
from ai.backend.manager.services.artifact.actions.get_revisions import (
    GetArtifactRevisionsAction,
)
from ai.backend.manager.services.artifact.actions.list_with_revisions import (
    ListArtifactsWithRevisionsAction,
)
from ai.backend.manager.services.artifact.actions.restore_multi import (
    RestoreArtifactsAction,
)
from ai.backend.manager.services.artifact.actions.retrieve_model import (
    RetrieveModelAction,
)
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import (
    RetrieveModelsAction,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
)
from ai.backend.manager.services.artifact.actions.search import (
    SearchArtifactsAction,
)
from ai.backend.manager.services.artifact.actions.search_with_revisions import (
    SearchArtifactsWithRevisionsAction,
)
from ai.backend.manager.services.artifact.actions.update import (
    UpdateArtifactAction,
)
from ai.backend.manager.services.artifact.actions.upsert_multi import (
    UpsertArtifactsAction,
)
from ai.backend.manager.services.artifact.service import ArtifactService
from ai.backend.manager.types import (
    OffsetBasedPaginationOptions,
    PaginationOptions,
    TriState,
)


class TestArtifactService:
    """Test cases for ArtifactService (artifact-only operations)"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        """Create mocked ArtifactRepository"""
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        """Create mocked ArtifactRegistryRepository"""
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def mock_object_storage_repository(self) -> MagicMock:
        """Create mocked ObjectStorageRepository"""
        return MagicMock(spec=ObjectStorageRepository)

    @pytest.fixture
    def mock_vfs_storage_repository(self) -> MagicMock:
        """Create mocked VFSStorageRepository"""
        return MagicMock(spec=VFSStorageRepository)

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        """Create mocked HuggingFaceRepository"""
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        """Create mocked ReservoirRegistryRepository"""
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        """Create mocked StorageSessionManager"""
        return MagicMock()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        """Create mocked ManagerConfigProvider"""
        return MagicMock()

    @pytest.fixture
    def artifact_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_vfs_storage_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
    ) -> ArtifactService:
        """Create ArtifactService instance with mocked repositories"""
        return ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=mock_object_storage_repository,
            vfs_storage_repository=mock_vfs_storage_repository,
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_registry_repository=mock_reservoir_repository,
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
        )

    @pytest.fixture
    def sample_artifact_data(self) -> ArtifactData:
        """Create sample artifact data"""
        now = datetime.now(UTC)
        registry_id = uuid4()
        return ArtifactData(
            id=uuid4(),
            name="microsoft/DialoGPT-medium",
            type=ArtifactType.MODEL,
            description="A conversational AI model by Microsoft",
            registry_id=registry_id,
            source_registry_id=registry_id,
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
        )

    async def test_get_artifact(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test getting an artifact by ID"""
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=sample_artifact_data)

        action = GetArtifactAction(artifact_id=sample_artifact_data.id)
        result = await artifact_service.get(action)

        assert result.result == sample_artifact_data
        mock_artifact_repository.get_artifact_by_id.assert_called_once_with(sample_artifact_data.id)

    async def test_search_artifacts(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test searching artifacts with querier"""
        mock_artifact_repository.search_artifacts = AsyncMock(
            return_value=ArtifactListResult(
                items=[sample_artifact_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactsAction(querier=querier)
        result = await artifact_service.search(action)

        assert result.data == [sample_artifact_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_artifact_repository.search_artifacts.assert_called_once_with(querier=querier)

    async def test_search_artifacts_empty_result(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Test searching artifacts when no results are found"""
        mock_artifact_repository.search_artifacts = AsyncMock(
            return_value=ArtifactListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactsAction(querier=querier)
        result = await artifact_service.search(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_artifacts_with_pagination(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test searching artifacts with pagination"""
        mock_artifact_repository.search_artifacts = AsyncMock(
            return_value=ArtifactListResult(
                items=[sample_artifact_data],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactsAction(querier=querier)
        result = await artifact_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True

    async def test_update_artifact(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test updating an artifact"""
        updater_spec = ArtifactUpdaterSpec(
            description=TriState.update("Updated description"),
        )
        updater = Updater[ArtifactRow](
            spec=updater_spec,
            pk_value=sample_artifact_data.id,
        )
        updated_artifact = ArtifactData(
            id=sample_artifact_data.id,
            name=sample_artifact_data.name,
            type=sample_artifact_data.type,
            description="Updated description",
            registry_id=sample_artifact_data.registry_id,
            source_registry_id=sample_artifact_data.source_registry_id,
            registry_type=sample_artifact_data.registry_type,
            source_registry_type=sample_artifact_data.source_registry_type,
            availability=sample_artifact_data.availability,
            scanned_at=sample_artifact_data.scanned_at,
            updated_at=datetime.now(UTC),
            readonly=sample_artifact_data.readonly,
            extra=sample_artifact_data.extra,
        )
        mock_artifact_repository.update_artifact = AsyncMock(return_value=updated_artifact)

        action = UpdateArtifactAction(updater=updater)
        result = await artifact_service.update(action)

        assert result.result.description == "Updated description"
        mock_artifact_repository.update_artifact.assert_called_once_with(updater)

    async def test_delete_artifacts(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test deleting artifacts"""
        deleted_artifact = ArtifactData(
            id=sample_artifact_data.id,
            name=sample_artifact_data.name,
            type=sample_artifact_data.type,
            description=sample_artifact_data.description,
            registry_id=sample_artifact_data.registry_id,
            source_registry_id=sample_artifact_data.source_registry_id,
            registry_type=sample_artifact_data.registry_type,
            source_registry_type=sample_artifact_data.source_registry_type,
            availability=ArtifactAvailability.DELETED,
            scanned_at=sample_artifact_data.scanned_at,
            updated_at=datetime.now(UTC),
            readonly=sample_artifact_data.readonly,
            extra=sample_artifact_data.extra,
        )
        mock_artifact_repository.delete_artifacts = AsyncMock(return_value=[deleted_artifact])

        action = DeleteArtifactsAction(artifact_ids=[sample_artifact_data.id])
        result = await artifact_service.delete_artifacts(action)

        assert len(result.artifacts) == 1
        assert result.artifacts[0].availability == ArtifactAvailability.DELETED
        mock_artifact_repository.delete_artifacts.assert_called_once_with([sample_artifact_data.id])

    async def test_restore_artifacts(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test restoring deleted artifacts"""
        mock_artifact_repository.restore_artifacts = AsyncMock(return_value=[sample_artifact_data])

        action = RestoreArtifactsAction(artifact_ids=[sample_artifact_data.id])
        result = await artifact_service.restore_artifacts(action)

        assert len(result.artifacts) == 1
        assert result.artifacts[0].availability == ArtifactAvailability.ALIVE
        mock_artifact_repository.restore_artifacts.assert_called_once_with([
            sample_artifact_data.id
        ])


class TestUpsertArtifactsAction:
    """Test cases for UpsertArtifactsAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def artifact_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
    ) -> ArtifactService:
        return ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=MagicMock(spec=ObjectStorageRepository),
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
        )

    def _make_artifact_with_revisions(
        self,
        *,
        artifact_id: None | object = None,
        registry_id: None | object = None,
        name: str = "test-model",
        num_revisions: int = 1,
    ) -> ArtifactDataWithRevisions:
        now = datetime.now(UTC)
        _artifact_id = artifact_id if artifact_id is not None else uuid4()
        _registry_id = registry_id if registry_id is not None else uuid4()
        revisions = [
            ArtifactRevisionData(
                id=uuid4(),
                artifact_id=_artifact_id,  # type: ignore[arg-type]
                version=f"v{i + 1}",
                readme=None,
                size=1000 * (i + 1),
                status=ArtifactStatus.SCANNED,
                remote_status=None,
                created_at=now,
                updated_at=now,
                digest=None,
                verification_result=None,
            )
            for i in range(num_revisions)
        ]
        return ArtifactDataWithRevisions(
            id=_artifact_id,  # type: ignore[arg-type]
            name=name,
            type=ArtifactType.MODEL,
            description=None,
            registry_id=_registry_id,  # type: ignore[arg-type]
            source_registry_id=_registry_id,  # type: ignore[arg-type]
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
            revisions=revisions,
        )

    async def test_single_artifact_upsert(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Single artifact+revision upsert succeeds with combined result"""
        data = self._make_artifact_with_revisions()
        upserted_artifact = ArtifactData(
            id=data.id,
            name=data.name,
            type=data.type,
            description=data.description,
            registry_id=data.registry_id,
            source_registry_id=data.source_registry_id,
            registry_type=data.registry_type,
            source_registry_type=data.source_registry_type,
            availability=data.availability,
            scanned_at=data.scanned_at,
            updated_at=data.updated_at,
            readonly=data.readonly,
            extra=data.extra,
        )
        mock_artifact_repository.upsert_artifacts = AsyncMock(return_value=[upserted_artifact])
        mock_artifact_repository.upsert_artifact_revisions = AsyncMock(return_value=data.revisions)

        action = UpsertArtifactsAction(data=[data])
        result = await artifact_service.upsert_artifacts_with_revisions(action)

        assert len(result.result) == 1
        assert result.result[0].id == data.id
        assert len(result.result[0].revisions) == 1
        mock_artifact_repository.upsert_artifacts.assert_called_once()
        mock_artifact_repository.upsert_artifact_revisions.assert_called_once()

    async def test_multiple_artifacts_grouped_per_revision(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Multiple artifacts grouped correctly per revision"""
        data1 = self._make_artifact_with_revisions(name="model-a", num_revisions=2)
        data2 = self._make_artifact_with_revisions(name="model-b", num_revisions=1)

        def upsert_artifacts_side_effect(artifacts: list) -> list[ArtifactData]:
            a = artifacts[0]
            return [
                ArtifactData(
                    id=a.id,
                    name=a.name,
                    type=a.type,
                    description=a.description,
                    registry_id=a.registry_id,
                    source_registry_id=a.source_registry_id,
                    registry_type=a.registry_type,
                    source_registry_type=a.source_registry_type,
                    availability=a.availability,
                    scanned_at=a.scanned_at,
                    updated_at=a.updated_at,
                    readonly=a.readonly,
                    extra=a.extra,
                )
            ]

        mock_artifact_repository.upsert_artifacts = AsyncMock(
            side_effect=upsert_artifacts_side_effect
        )
        mock_artifact_repository.upsert_artifact_revisions = AsyncMock(
            side_effect=lambda revisions: revisions
        )

        action = UpsertArtifactsAction(data=[data1, data2])
        result = await artifact_service.upsert_artifacts_with_revisions(action)

        assert len(result.result) == 2
        assert len(result.result[0].revisions) == 2
        assert len(result.result[1].revisions) == 1
        assert mock_artifact_repository.upsert_artifacts.call_count == 2

    async def test_existing_artifact_updated(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Existing artifact updated via upsert"""
        data = self._make_artifact_with_revisions(name="existing-model")
        updated = ArtifactData(
            id=data.id,
            name=data.name,
            type=data.type,
            description="Updated via upsert",
            registry_id=data.registry_id,
            source_registry_id=data.source_registry_id,
            registry_type=data.registry_type,
            source_registry_type=data.source_registry_type,
            availability=data.availability,
            scanned_at=data.scanned_at,
            updated_at=datetime.now(UTC),
            readonly=data.readonly,
            extra=data.extra,
        )
        mock_artifact_repository.upsert_artifacts = AsyncMock(return_value=[updated])
        mock_artifact_repository.upsert_artifact_revisions = AsyncMock(return_value=data.revisions)

        action = UpsertArtifactsAction(data=[data])
        result = await artifact_service.upsert_artifacts_with_revisions(action)

        assert result.result[0].description == "Updated via upsert"


class TestScanArtifactsAction:
    """Test cases for ScanArtifactsAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def mock_object_storage_repository(self) -> MagicMock:
        return MagicMock(spec=ObjectStorageRepository)

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        provider = MagicMock()
        provider.config.reservoir.archive_storage = "test-storage"
        provider.config.artifact_registry.model_registry = "default-registry"
        return provider

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def artifact_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_config_provider: MagicMock,
        mock_storage_manager: MagicMock,
    ) -> ArtifactService:
        return ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=mock_object_storage_repository,
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_registry_repository=mock_reservoir_repository,
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
        )

    @pytest.fixture
    def registry_id(self) -> object:
        return uuid4()

    @pytest.fixture
    def hf_registry_meta(self, registry_id: object) -> ArtifactRegistryData:
        return ArtifactRegistryData(
            id=uuid4(),
            registry_id=registry_id,  # type: ignore[arg-type]
            name="huggingface-default",
            type=ArtifactRegistryType.HUGGINGFACE,
        )

    async def test_huggingface_without_limit_order_raises(
        self,
        artifact_service: ArtifactService,
        mock_artifact_registry_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_huggingface_repository: MagicMock,
        registry_id: object,
        hf_registry_meta: ArtifactRegistryData,
    ) -> None:
        """HuggingFace without limit/order raises ArtifactRegistryBadScanRequestError"""
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=hf_registry_meta
        )
        mock_object_storage_repository.get_by_name = AsyncMock(return_value=MagicMock(host="h"))
        mock_storage_manager.get_manager_facing_client = MagicMock(return_value=MagicMock())
        mock_huggingface_repository.get_registry_data_by_id = AsyncMock(
            return_value=HuggingFaceRegistryData(
                id=registry_id, name="hf", url="https://huggingface.co", token=None
            )
        )

        action = ScanArtifactsAction(
            artifact_type=ArtifactType.MODEL,
            registry_id=registry_id,  # type: ignore[arg-type]
            limit=None,
            order=None,
            search=None,
        )
        with pytest.raises(ArtifactRegistryBadScanRequestError):
            await artifact_service.scan(action)

    async def test_huggingface_valid_scan_upserts(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_huggingface_repository: MagicMock,
        registry_id: object,
        hf_registry_meta: ArtifactRegistryData,
    ) -> None:
        """Valid limit/order upserts scanned models"""
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=hf_registry_meta
        )

        mock_storage_client = AsyncMock()
        scan_resp = MagicMock()
        scan_resp.models = [MagicMock()]
        mock_storage_client.scan_huggingface_models = AsyncMock(return_value=scan_resp)

        mock_object_storage_repository.get_by_name = AsyncMock(return_value=MagicMock(host="h"))
        mock_storage_manager.get_manager_facing_client = MagicMock(return_value=mock_storage_client)

        now = datetime.now(UTC)
        expected_result = [
            ArtifactDataWithRevisions(
                id=uuid4(),
                name="model-1",
                type=ArtifactType.MODEL,
                description=None,
                registry_id=registry_id,  # type: ignore[arg-type]
                source_registry_id=registry_id,  # type: ignore[arg-type]
                registry_type=ArtifactRegistryType.HUGGINGFACE,
                source_registry_type=ArtifactRegistryType.HUGGINGFACE,
                availability=ArtifactAvailability.ALIVE,
                scanned_at=now,
                updated_at=now,
                readonly=True,
                extra=None,
                revisions=[],
            )
        ]
        mock_artifact_repository.upsert_huggingface_model_artifacts = AsyncMock(
            return_value=expected_result
        )
        mock_huggingface_repository.get_registry_data_by_id = AsyncMock(
            return_value=HuggingFaceRegistryData(
                id=registry_id, name="hf", url="https://huggingface.co", token=None
            )
        )

        action = ScanArtifactsAction(
            artifact_type=ArtifactType.MODEL,
            registry_id=registry_id,  # type: ignore[arg-type]
            limit=10,
            order=ModelSortKey.LAST_MODIFIED,
            search=None,
        )
        result = await artifact_service.scan(action)

        assert len(result.result) == 1
        mock_artifact_repository.upsert_huggingface_model_artifacts.assert_called_once()

    async def test_reservoir_timeout_raises_connection_error(
        self,
        artifact_service: ArtifactService,
        mock_artifact_registry_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        """Reservoir timeout raises ReservoirConnectionError (MAX_RETRIES=3)"""
        reservoir_registry_id = uuid4()
        reservoir_meta = ArtifactRegistryData(
            id=uuid4(),
            registry_id=reservoir_registry_id,
            name="reservoir-default",
            type=ArtifactRegistryType.RESERVOIR,
        )
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=reservoir_meta
        )
        mock_object_storage_repository.get_by_name = AsyncMock(return_value=MagicMock(host="h"))
        mock_storage_manager.get_manager_facing_client = MagicMock(return_value=MagicMock())

        reservoir_data = MagicMock()
        reservoir_data.endpoint = "http://remote:8080"
        mock_reservoir_repository.get_reservoir_registry_data_by_id = AsyncMock(
            return_value=reservoir_data
        )

        conn_error = ClientConnectorError(
            connection_key=MagicMock(), os_error=OSError("Connection refused")
        )

        with patch(
            "ai.backend.manager.services.artifact.service.ReservoirRegistryClient"
        ) as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.search_artifacts = AsyncMock(side_effect=conn_error)
            MockClient.return_value = mock_client_instance

            action = ScanArtifactsAction(
                artifact_type=ArtifactType.MODEL,
                registry_id=reservoir_registry_id,
                limit=10,
                order=ModelSortKey.LAST_MODIFIED,
                search=None,
            )
            with pytest.raises(ReservoirConnectionError):
                await artifact_service.scan(action)

            assert mock_client_instance.search_artifacts.call_count == 3

    async def test_registry_id_none_uses_default_registry(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_huggingface_repository: MagicMock,
        hf_registry_meta: ArtifactRegistryData,
    ) -> None:
        """registry_id=None uses default registry from config"""
        mock_artifact_registry_repository.get_artifact_registry_data_by_name = AsyncMock(
            return_value=hf_registry_meta
        )
        mock_huggingface_repository.get_registry_data_by_id = AsyncMock(
            return_value=HuggingFaceRegistryData(
                id=hf_registry_meta.registry_id, name="hf", url="https://huggingface.co", token=None
            )
        )

        mock_storage_client = AsyncMock()
        scan_resp = MagicMock()
        scan_resp.models = []
        mock_storage_client.scan_huggingface_models = AsyncMock(return_value=scan_resp)
        mock_object_storage_repository.get_by_name = AsyncMock(return_value=MagicMock(host="h"))
        mock_storage_manager.get_manager_facing_client = MagicMock(return_value=mock_storage_client)
        mock_artifact_repository.upsert_huggingface_model_artifacts = AsyncMock(return_value=[])

        action = ScanArtifactsAction(
            artifact_type=ArtifactType.MODEL,
            registry_id=None,
            limit=5,
            order=ModelSortKey.DOWNLOADS,
            search=None,
        )
        result = await artifact_service.scan(action)

        mock_artifact_registry_repository.get_artifact_registry_data_by_name.assert_called_once_with(
            "default-registry"
        )
        assert result.result == []


class TestDelegateScanArtifactsAction:
    """Test cases for DelegateScanArtifactsAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def mock_config_provider_leaf(self) -> MagicMock:
        provider = MagicMock()
        provider.config.reservoir.archive_storage = "test-storage"
        provider.config.reservoir.use_delegation = False
        provider.config.artifact_registry.model_registry = "default-registry"
        return provider

    @pytest.fixture
    def mock_config_provider_delegator(self) -> MagicMock:
        provider = MagicMock()
        provider.config.reservoir.archive_storage = "test-storage"
        provider.config.reservoir.use_delegation = True
        provider.config.artifact_registry.model_registry = "default-registry"
        return provider

    def _build_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        config_provider: MagicMock,
        object_storage_repository: MagicMock | None = None,
        storage_manager: MagicMock | None = None,
    ) -> ArtifactService:
        return ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=object_storage_repository
            or MagicMock(spec=ObjectStorageRepository),
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_registry_repository=mock_reservoir_repository,
            storage_manager=storage_manager or MagicMock(),
            config_provider=config_provider,
        )

    async def test_leaf_scan_includes_source_registry_and_readme(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_config_provider_leaf: MagicMock,
    ) -> None:
        """Remote Reservoir scan result includes source_registry_id/readme_data (leaf node)"""
        now = datetime.now(UTC)
        target_registry_id = uuid4()

        hf_meta = ArtifactRegistryData(
            id=uuid4(),
            registry_id=target_registry_id,
            name="hf-default",
            type=ArtifactRegistryType.HUGGINGFACE,
        )
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=hf_meta
        )

        revision_id = uuid4()
        artifact_id = uuid4()
        scan_result_artifacts = [
            ArtifactDataWithRevisions(
                id=artifact_id,
                name="test-model",
                type=ArtifactType.MODEL,
                description=None,
                registry_id=target_registry_id,
                source_registry_id=target_registry_id,
                registry_type=ArtifactRegistryType.HUGGINGFACE,
                source_registry_type=ArtifactRegistryType.HUGGINGFACE,
                availability=ArtifactAvailability.ALIVE,
                scanned_at=now,
                updated_at=now,
                readonly=True,
                extra=None,
                revisions=[
                    ArtifactRevisionData(
                        id=revision_id,
                        artifact_id=artifact_id,
                        version="v1",
                        readme="# Test README",
                        size=1000,
                        status=ArtifactStatus.SCANNED,
                        remote_status=None,
                        created_at=now,
                        updated_at=now,
                        digest=None,
                        verification_result=None,
                    )
                ],
            )
        ]

        mock_obj_storage = MagicMock(spec=ObjectStorageRepository)
        mock_obj_storage.get_by_name = AsyncMock(return_value=MagicMock(host="h"))
        mock_storage_mgr = MagicMock()

        mock_storage_client = AsyncMock()
        scan_resp = MagicMock()
        scan_resp.models = [MagicMock()]
        mock_storage_client.scan_huggingface_models = AsyncMock(return_value=scan_resp)
        mock_storage_mgr.get_manager_facing_client = MagicMock(return_value=mock_storage_client)

        mock_hf_repo = MagicMock(spec=HuggingFaceRepository)
        mock_hf_repo.get_registry_data_by_id = AsyncMock(
            return_value=HuggingFaceRegistryData(
                id=target_registry_id, name="hf", url="https://huggingface.co", token=None
            )
        )
        mock_artifact_repository.upsert_huggingface_model_artifacts = AsyncMock(
            return_value=scan_result_artifacts
        )

        service = ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=mock_obj_storage,
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            huggingface_registry_repository=mock_hf_repo,
            reservoir_registry_repository=mock_reservoir_repository,
            storage_manager=mock_storage_mgr,
            config_provider=mock_config_provider_leaf,
        )

        delegatee_target = DelegateeTarget(
            delegatee_reservoir_id=uuid4(),
            target_registry_id=target_registry_id,
        )
        action = DelegateScanArtifactsAction(
            delegator_reservoir_id=None,
            artifact_type=ArtifactType.MODEL,
            search=None,
            order=ModelSortKey.LAST_MODIFIED,
            delegatee_target=delegatee_target,
            limit=10,
        )
        result = await service.delegate_scan_artifacts(action)

        assert result.source_registry_id == target_registry_id
        assert result.source_registry_type == ArtifactRegistryType.HUGGINGFACE
        assert revision_id in result.readme_data
        assert result.readme_data[revision_id].readme == "# Test README"

    async def test_remote_connection_failure_raises_remote_scan_error(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_config_provider_leaf: MagicMock,
    ) -> None:
        """Remote connection failure raises RemoteReservoirScanError (leaf)"""
        mock_config_provider_leaf.config.reservoir = None

        service = self._build_service(
            mock_artifact_repository,
            mock_artifact_registry_repository,
            mock_reservoir_repository,
            mock_config_provider_leaf,
        )

        action = DelegateScanArtifactsAction(
            delegator_reservoir_id=None,
            artifact_type=ArtifactType.MODEL,
            search=None,
            order=ModelSortKey.LAST_MODIFIED,
            delegatee_target=None,
            limit=10,
        )
        with pytest.raises(ServerMisconfiguredError):
            await service.delegate_scan_artifacts(action)


class TestRetrieveModelAction:
    """Test cases for RetrieveModelAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        provider = MagicMock()
        provider.config.reservoir.archive_storage = "test-storage"
        return provider

    @pytest.fixture
    def mock_object_storage_repository(self) -> MagicMock:
        return MagicMock(spec=ObjectStorageRepository)

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def artifact_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_config_provider: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_manager: MagicMock,
    ) -> ArtifactService:
        return ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=mock_object_storage_repository,
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
        )

    async def test_huggingface_single_model_retrieval(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_manager: MagicMock,
    ) -> None:
        """HuggingFace single model retrieval + upsert"""
        now = datetime.now(UTC)
        registry_id = uuid4()
        hf_meta = ArtifactRegistryData(
            id=uuid4(),
            registry_id=registry_id,
            name="hf-registry",
            type=ArtifactRegistryType.HUGGINGFACE,
        )
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=hf_meta
        )
        mock_huggingface_repository.get_registry_data_by_id = AsyncMock(
            return_value=HuggingFaceRegistryData(
                id=registry_id, name="hf", url="https://huggingface.co", token=None
            )
        )

        mock_storage_client = AsyncMock()
        resp = MagicMock()
        resp.model = MagicMock()
        mock_storage_client.retrieve_huggingface_model = AsyncMock(return_value=resp)
        mock_object_storage_repository.get_by_name = AsyncMock(return_value=MagicMock(host="h"))
        mock_storage_manager.get_manager_facing_client = MagicMock(return_value=mock_storage_client)

        expected = ArtifactDataWithRevisions(
            id=uuid4(),
            name="gpt2",
            type=ArtifactType.MODEL,
            description=None,
            registry_id=registry_id,
            source_registry_id=registry_id,
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
            revisions=[],
        )
        mock_artifact_repository.upsert_huggingface_model_artifacts = AsyncMock(
            return_value=[expected]
        )

        model = ModelTarget(model_id="openai/gpt-2")
        action = RetrieveModelAction(registry_id=registry_id, model=model)
        result = await artifact_service.retrieve_single_model(action)

        assert result.result.name == "gpt2"
        mock_artifact_repository.upsert_huggingface_model_artifacts.assert_called_once()

    async def test_reservoir_raises_not_implemented(
        self,
        artifact_service: ArtifactService,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        """Reservoir raises NotImplementedError"""
        registry_id = uuid4()
        reservoir_meta = ArtifactRegistryData(
            id=uuid4(),
            registry_id=registry_id,
            name="reservoir-reg",
            type=ArtifactRegistryType.RESERVOIR,
        )
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=reservoir_meta
        )

        model = ModelTarget(model_id="some-model")
        action = RetrieveModelAction(registry_id=registry_id, model=model)
        with pytest.raises(NotImplementedError):
            await artifact_service.retrieve_single_model(action)

    async def test_no_storage_config_raises_misconfigured(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        """No storage config raises ServerMisconfiguredError"""
        config_provider = MagicMock()
        config_provider.config.reservoir = None

        registry_id = uuid4()
        hf_meta = ArtifactRegistryData(
            id=uuid4(),
            registry_id=registry_id,
            name="hf-reg",
            type=ArtifactRegistryType.HUGGINGFACE,
        )
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=hf_meta
        )

        service = ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=MagicMock(spec=ObjectStorageRepository),
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            storage_manager=MagicMock(),
            config_provider=config_provider,
        )

        model = ModelTarget(model_id="openai/gpt-2")
        action = RetrieveModelAction(registry_id=registry_id, model=model)
        with pytest.raises(ServerMisconfiguredError):
            await service.retrieve_single_model(action)


class TestRetrieveModelsAction:
    """Test cases for RetrieveModelsAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        provider = MagicMock()
        provider.config.reservoir.archive_storage = "test-storage"
        return provider

    @pytest.fixture
    def artifact_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_config_provider: MagicMock,
    ) -> ArtifactService:
        mock_obj = MagicMock(spec=ObjectStorageRepository)
        mock_obj.get_by_name = AsyncMock(return_value=MagicMock(host="h"))
        mock_storage_mgr = MagicMock()
        return ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=mock_obj,
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            storage_manager=mock_storage_mgr,
            config_provider=mock_config_provider,
        )

    async def test_multiple_huggingface_models_batch_retrieval(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        """Multiple HuggingFace models batch retrieval + upsert"""
        now = datetime.now(UTC)
        registry_id = uuid4()
        hf_meta = ArtifactRegistryData(
            id=uuid4(),
            registry_id=registry_id,
            name="hf-registry",
            type=ArtifactRegistryType.HUGGINGFACE,
        )
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=hf_meta
        )
        mock_huggingface_repository.get_registry_data_by_id = AsyncMock(
            return_value=HuggingFaceRegistryData(
                id=registry_id, name="hf", url="https://huggingface.co", token=None
            )
        )

        mock_storage_client = AsyncMock()
        resp = MagicMock()
        resp.models = [MagicMock(), MagicMock()]
        mock_storage_client.retrieve_huggingface_models = AsyncMock(return_value=resp)
        artifact_service._storage_manager.get_manager_facing_client = MagicMock(
            return_value=mock_storage_client
        )

        expected = [
            ArtifactDataWithRevisions(
                id=uuid4(),
                name=f"model-{i}",
                type=ArtifactType.MODEL,
                description=None,
                registry_id=registry_id,
                source_registry_id=registry_id,
                registry_type=ArtifactRegistryType.HUGGINGFACE,
                source_registry_type=ArtifactRegistryType.HUGGINGFACE,
                availability=ArtifactAvailability.ALIVE,
                scanned_at=now,
                updated_at=now,
                readonly=True,
                extra=None,
                revisions=[],
            )
            for i in range(2)
        ]
        mock_artifact_repository.upsert_huggingface_model_artifacts = AsyncMock(
            return_value=expected
        )

        models = [
            ModelTarget(model_id="model-a"),
            ModelTarget(model_id="model-b"),
        ]
        action = RetrieveModelsAction(registry_id=registry_id, models=models)
        result = await artifact_service.retrieve_models(action)

        assert len(result.result) == 2
        mock_storage_client.retrieve_huggingface_models.assert_called_once()


class TestGetArtifactRevisionsAction:
    """Test cases for GetArtifactRevisionsAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def artifact_service(self, mock_artifact_repository: MagicMock) -> ArtifactService:
        return ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
            object_storage_repository=MagicMock(spec=ObjectStorageRepository),
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
        )

    async def test_artifact_with_multiple_versions(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Artifact with multiple versions returns sorted revision list"""
        now = datetime.now(UTC)
        artifact_id = uuid4()
        revisions = [
            ArtifactRevisionData(
                id=uuid4(),
                artifact_id=artifact_id,
                version=f"v{i}",
                readme=None,
                size=1000 * i,
                status=ArtifactStatus.AVAILABLE,
                remote_status=None,
                created_at=now,
                updated_at=now,
                digest=None,
                verification_result=None,
            )
            for i in range(3)
        ]
        mock_artifact_repository.list_artifact_revisions = AsyncMock(return_value=revisions)

        action = GetArtifactRevisionsAction(artifact_id=artifact_id)
        result = await artifact_service.get_revisions(action)

        assert len(result.revisions) == 3
        mock_artifact_repository.list_artifact_revisions.assert_called_once_with(artifact_id)

    async def test_no_revisions_returns_empty(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """No revisions returns empty list"""
        mock_artifact_repository.list_artifact_revisions = AsyncMock(return_value=[])

        action = GetArtifactRevisionsAction(artifact_id=uuid4())
        result = await artifact_service.get_revisions(action)

        assert result.revisions == []


class TestListArtifactsWithRevisionsAction:
    """Test cases for ListArtifactsWithRevisionsAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def artifact_service(self, mock_artifact_repository: MagicMock) -> ArtifactService:
        return ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
            object_storage_repository=MagicMock(spec=ObjectStorageRepository),
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
        )

    def _make_artifact_with_revisions(self, name: str) -> ArtifactDataWithRevisions:
        now = datetime.now(UTC)
        rid = uuid4()
        return ArtifactDataWithRevisions(
            id=uuid4(),
            name=name,
            type=ArtifactType.MODEL,
            description=None,
            registry_id=rid,
            source_registry_id=rid,
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
            revisions=[],
        )

    async def test_pagination_returns_correct_subset(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Pagination (offset/limit) returns correct subset + total_count"""
        items = [self._make_artifact_with_revisions(f"m{i}") for i in range(3)]
        mock_artifact_repository.list_artifacts_with_revisions_paginated = AsyncMock(
            return_value=(items, 10)
        )

        pagination = PaginationOptions(offset=OffsetBasedPaginationOptions(offset=0, limit=3))
        action = ListArtifactsWithRevisionsAction(pagination=pagination)
        result = await artifact_service.list_with_revisions(action)

        assert len(result.data) == 3
        assert result.total_count == 10

    async def test_name_type_filter_applied(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Name/type filter applied"""
        items = [self._make_artifact_with_revisions("filtered-model")]
        mock_artifact_repository.list_artifacts_with_revisions_paginated = AsyncMock(
            return_value=(items, 1)
        )

        filters = ArtifactFilterOptions(artifact_type=[ArtifactType.MODEL])
        action = ListArtifactsWithRevisionsAction(filters=filters)
        result = await artifact_service.list_with_revisions(action)

        assert len(result.data) == 1
        call_kwargs = mock_artifact_repository.list_artifacts_with_revisions_paginated.call_args
        assert call_kwargs.kwargs["filters"] == filters

    async def test_pagination_none_returns_all(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Pagination=None returns all"""
        items = [self._make_artifact_with_revisions(f"m{i}") for i in range(5)]
        mock_artifact_repository.list_artifacts_with_revisions_paginated = AsyncMock(
            return_value=(items, 5)
        )

        action = ListArtifactsWithRevisionsAction(pagination=None)
        result = await artifact_service.list_with_revisions(action)

        assert len(result.data) == 5
        assert result.total_count == 5


class TestSearchArtifactsWithRevisionsAction:
    """Test cases for SearchArtifactsWithRevisionsAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def artifact_service(self, mock_artifact_repository: MagicMock) -> ArtifactService:
        return ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
            object_storage_repository=MagicMock(spec=ObjectStorageRepository),
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
        )

    async def test_cursor_pagination_sets_has_next_previous(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """BatchQuerier cursor-based pagination sets has_next_page/has_previous_page"""
        now = datetime.now(UTC)
        rid = uuid4()
        item = ArtifactDataWithRevisions(
            id=uuid4(),
            name="test-model",
            type=ArtifactType.MODEL,
            description=None,
            registry_id=rid,
            source_registry_id=rid,
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
            revisions=[],
        )
        mock_artifact_repository.search_artifacts_with_revisions = AsyncMock(
            return_value=ArtifactWithRevisionsListResult(
                items=[item],
                total_count=20,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1, offset=5),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactsWithRevisionsAction(querier=querier)
        result = await artifact_service.search_with_revisions(action)

        assert result.has_next_page is True
        assert result.has_previous_page is True
        assert result.total_count == 20
        assert len(result.data) == 1

    async def test_no_match_returns_empty(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """No match returns empty data + total_count=0"""
        mock_artifact_repository.search_artifacts_with_revisions = AsyncMock(
            return_value=ArtifactWithRevisionsListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactsWithRevisionsAction(querier=querier)
        result = await artifact_service.search_with_revisions(action)

        assert result.data == []
        assert result.total_count == 0
        assert result.has_next_page is False
        assert result.has_previous_page is False
