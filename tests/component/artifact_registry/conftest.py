from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.artifact_registry.handler import ArtifactRegistryHandler
from ai.backend.manager.api.rest.artifact_registry.registry import (
    register_artifact_registry_routes,
)
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.artifact.processors import ArtifactProcessors
from ai.backend.manager.services.artifact.service import ArtifactService
from ai.backend.manager.services.artifact_revision.processors import ArtifactRevisionProcessors
from ai.backend.manager.services.artifact_revision.service import ArtifactRevisionService


@dataclass
class RegistryFixtureData:
    huggingface_registry_id: uuid.UUID
    reservoir_registry_id: uuid.UUID
    hf_artifact_id: uuid.UUID
    hf_revision_id: uuid.UUID
    reservoir_artifact_id: uuid.UUID
    reservoir_revision_id: uuid.UUID


RegistryFactory = Callable[..., Coroutine[Any, Any, RegistryFixtureData]]


@pytest.fixture()
def artifact_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: StorageSessionManager,
    config_provider: ManagerConfigProvider,
) -> ArtifactProcessors:
    artifact_repository = ArtifactRepository(database_engine)
    artifact_registry_repository = ArtifactRegistryRepository(database_engine)
    object_storage_repository = ObjectStorageRepository(database_engine)
    vfs_storage_repository = VFSStorageRepository(database_engine)
    huggingface_repository = HuggingFaceRepository(database_engine)
    reservoir_repository = ReservoirRegistryRepository(database_engine)
    service = ArtifactService(
        artifact_repository=artifact_repository,
        artifact_registry_repository=artifact_registry_repository,
        object_storage_repository=object_storage_repository,
        vfs_storage_repository=vfs_storage_repository,
        huggingface_registry_repository=huggingface_repository,
        reservoir_registry_repository=reservoir_repository,
        storage_manager=storage_manager,
        config_provider=config_provider,
    )
    return ArtifactProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def artifact_revision_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: StorageSessionManager,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    background_task_manager: BackgroundTaskManager,
) -> ArtifactRevisionProcessors:
    artifact_repository = ArtifactRepository(database_engine)
    artifact_registry_repository = ArtifactRegistryRepository(database_engine)
    object_storage_repository = ObjectStorageRepository(database_engine)
    vfs_storage_repository = VFSStorageRepository(database_engine)
    storage_namespace_repository = StorageNamespaceRepository(database_engine)
    huggingface_repository = HuggingFaceRepository(database_engine)
    reservoir_repository = ReservoirRegistryRepository(database_engine)
    vfolder_repository = VfolderRepository(database_engine)
    service = ArtifactRevisionService(
        artifact_repository=artifact_repository,
        artifact_registry_repository=artifact_registry_repository,
        object_storage_repository=object_storage_repository,
        vfs_storage_repository=vfs_storage_repository,
        storage_namespace_repository=storage_namespace_repository,
        huggingface_registry_repository=huggingface_repository,
        reservoir_registry_repository=reservoir_repository,
        vfolder_repository=vfolder_repository,
        storage_manager=storage_manager,
        config_provider=config_provider,
        valkey_artifact_client=valkey_clients.artifact,
        background_task_manager=background_task_manager,
    )
    return ArtifactRevisionProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    artifact_processors: ArtifactProcessors,
    artifact_revision_processors: ArtifactRevisionProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for artifact-registry-domain tests."""
    return [
        register_artifact_registry_routes(
            ArtifactRegistryHandler(
                artifact=artifact_processors,
                artifact_revision=artifact_revision_processors,
            ),
            route_deps,
        ),
    ]


@pytest.fixture()
async def registry_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[RegistryFixtureData]:
    """Seed HuggingFace and Reservoir registries with artifacts in the DB."""
    hf_registry_id = uuid.uuid4()
    reservoir_registry_id = uuid.uuid4()
    hf_artifact_id = uuid.uuid4()
    hf_revision_id = uuid.uuid4()
    reservoir_artifact_id = uuid.uuid4()
    reservoir_revision_id = uuid.uuid4()
    hf_meta_id = uuid.uuid4()
    reservoir_meta_id = uuid.uuid4()

    async with db_engine.begin() as conn:
        # Create HuggingFace registry
        await conn.execute(
            sa.insert(HuggingFaceRegistryRow.__table__).values(
                id=hf_registry_id,
                url="https://huggingface.co",
                token=None,
            )
        )
        await conn.execute(
            sa.insert(ArtifactRegistryRow.__table__).values(
                id=hf_meta_id,
                name="test-hf-registry",
                registry_id=hf_registry_id,
                type=ArtifactRegistryType.HUGGINGFACE.value,
            )
        )
        # Create Reservoir registry
        await conn.execute(
            sa.insert(ReservoirRegistryRow.__table__).values(
                id=reservoir_registry_id,
                endpoint="https://reservoir.test.local",
                access_key="test-access",
                secret_key="test-secret",
                api_version="v1",
            )
        )
        await conn.execute(
            sa.insert(ArtifactRegistryRow.__table__).values(
                id=reservoir_meta_id,
                name="test-reservoir-registry",
                registry_id=reservoir_registry_id,
                type=ArtifactRegistryType.RESERVOIR.value,
            )
        )
        # Create artifacts for HuggingFace registry
        await conn.execute(
            sa.insert(ArtifactRow.__table__).values(
                id=hf_artifact_id,
                type=ArtifactType.MODEL,
                name="hf-test-model",
                registry_id=hf_registry_id,
                registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                source_registry_id=hf_registry_id,
                source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                description="HuggingFace test model",
                readonly=False,
                availability=ArtifactAvailability.ALIVE.value,
            )
        )
        await conn.execute(
            sa.insert(ArtifactRevisionRow.__table__).values(
                id=hf_revision_id,
                artifact_id=hf_artifact_id,
                version="main",
                status=ArtifactStatus.SCANNED.value,
            )
        )
        # Create artifacts for Reservoir registry
        await conn.execute(
            sa.insert(ArtifactRow.__table__).values(
                id=reservoir_artifact_id,
                type=ArtifactType.MODEL,
                name="reservoir-test-model",
                registry_id=reservoir_registry_id,
                registry_type=ArtifactRegistryType.RESERVOIR.value,
                source_registry_id=reservoir_registry_id,
                source_registry_type=ArtifactRegistryType.RESERVOIR.value,
                description="Reservoir test model",
                readonly=False,
                availability=ArtifactAvailability.ALIVE.value,
            )
        )
        await conn.execute(
            sa.insert(ArtifactRevisionRow.__table__).values(
                id=reservoir_revision_id,
                artifact_id=reservoir_artifact_id,
                version="v1.0",
                status=ArtifactStatus.SCANNED.value,
            )
        )

    yield RegistryFixtureData(
        huggingface_registry_id=hf_registry_id,
        reservoir_registry_id=reservoir_registry_id,
        hf_artifact_id=hf_artifact_id,
        hf_revision_id=hf_revision_id,
        reservoir_artifact_id=reservoir_artifact_id,
        reservoir_revision_id=reservoir_revision_id,
    )

    # Cleanup
    async with db_engine.begin() as conn:
        for aid in [hf_artifact_id, reservoir_artifact_id]:
            await conn.execute(
                sa.delete(ArtifactRevisionRow.__table__).where(
                    ArtifactRevisionRow.__table__.c.artifact_id == aid
                )
            )
            await conn.execute(
                sa.delete(ArtifactRow.__table__).where(ArtifactRow.__table__.c.id == aid)
            )
        await conn.execute(
            sa.delete(ArtifactRegistryRow.__table__).where(
                ArtifactRegistryRow.__table__.c.registry_id.in_([
                    hf_registry_id,
                    reservoir_registry_id,
                ])
            )
        )
        await conn.execute(
            sa.delete(HuggingFaceRegistryRow.__table__).where(
                HuggingFaceRegistryRow.__table__.c.id == hf_registry_id
            )
        )
        await conn.execute(
            sa.delete(ReservoirRegistryRow.__table__).where(
                ReservoirRegistryRow.__table__.c.id == reservoir_registry_id
            )
        )
