from unittest.mock import MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import (
    ObjectStorageRepository,  # pants: no-infer-dep
)
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.artifact_revision.processors import ArtifactRevisionProcessors
from ai.backend.manager.services.artifact_revision.service import ArtifactRevisionService


@pytest.fixture
def processors(extra_fixtures, database_fixture, database_engine, registry_ctx):
    artifact_repository = ArtifactRepository(database_engine)
    # Mock other dependencies for artifact revision service
    artifact_registry_repository = MagicMock(spec=ArtifactRegistryRepository)
    object_storage_repository = MagicMock(spec=ObjectStorageRepository)
    vfs_storage_repository = MagicMock(spec=VFSStorageRepository)
    storage_namespace_repository = MagicMock(spec=StorageNamespaceRepository)
    huggingface_registry_repository = MagicMock(spec=HuggingFaceRepository)
    reservoir_registry_repository = MagicMock(spec=ReservoirRegistryRepository)
    storage_manager = MagicMock()
    config_provider = MagicMock()
    valkey_artifact_client = MagicMock(spec=ValkeyArtifactDownloadTrackingClient)
    background_task_manager = MagicMock()

    artifact_revision_service = ArtifactRevisionService(
        artifact_repository=artifact_repository,
        artifact_registry_repository=artifact_registry_repository,
        object_storage_repository=object_storage_repository,
        vfs_storage_repository=vfs_storage_repository,
        storage_namespace_repository=storage_namespace_repository,
        huggingface_registry_repository=huggingface_registry_repository,
        reservoir_registry_repository=reservoir_registry_repository,
        storage_manager=storage_manager,
        config_provider=config_provider,
        valkey_artifact_client=valkey_artifact_client,
        background_task_manager=background_task_manager,
    )
    return ArtifactRevisionProcessors(artifact_revision_service, [])
