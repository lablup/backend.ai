from unittest.mock import MagicMock

import pytest

from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import (
    ObjectStorageRepository,  # pants: no-infer-dep
)
from ai.backend.manager.services.artifact_revision.processors import ArtifactRevisionProcessors
from ai.backend.manager.services.artifact_revision.service import ArtifactRevisionService


@pytest.fixture
def processors(extra_fixtures, database_fixture, database_engine, registry_ctx):
    artifact_repository = ArtifactRepository(database_engine)
    # Mock other dependencies for artifact revision service
    object_storage_repository = MagicMock(spec=ObjectStorageRepository)
    huggingface_registry_repository = MagicMock(spec=HuggingFaceRepository)
    storage_manager = MagicMock()

    artifact_revision_service = ArtifactRevisionService(
        artifact_repository=artifact_repository,
        object_storage_repository=object_storage_repository,
        huggingface_registry_repository=huggingface_registry_repository,
        storage_manager=storage_manager,
    )
    return ArtifactRevisionProcessors(artifact_revision_service, [])
