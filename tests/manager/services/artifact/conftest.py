import pytest

from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.services.artifact.processors import ArtifactProcessors
from ai.backend.manager.services.artifact.service import ArtifactService


@pytest.fixture
def processors(extra_fixtures, database_fixture, database_engine, storage_manager_ctx):
    artifact_repository = ArtifactRepository(database_engine)
    object_storage_repository = ObjectStorageRepository(database_engine)
    huggingface_registry_repository = HuggingFaceRepository(database_engine)
    storage_manager, _ = storage_manager_ctx

    artifact_service = ArtifactService(
        artifact_repository=artifact_repository,
        storage_manager=storage_manager,
        object_storage_repository=object_storage_repository,
        huggingface_registry_repository=huggingface_registry_repository,
    )
    return ArtifactProcessors(artifact_service, [])
