"""The artifact adapter, assembled for one row.

The only place in these scenarios that knows how the adapter is built. The registries,
the storages, the storage proxy and the background tasks are not wired: only scanning
and importing reach them.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.data.entity.artifact import ArtifactEntityType
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionFieldType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact_registry.repository import (
    ArtifactRegistryRepository,
)
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.repositories.storage_namespace.repository import (
    StorageNamespaceRepository,
)
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.artifact.processors import ArtifactProcessors
from ai.backend.manager.services.artifact.revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
    LookupBulkArtifactRevisionOwnerAction,
)
from ai.backend.manager.services.artifact.revision.processors import ArtifactRevisionProcessors
from ai.backend.manager.services.artifact.revision.service import ArtifactRevisionService
from ai.backend.manager.services.artifact.service import ArtifactService
from bai_scenario.runner.unwired import unwired

_SCANNING = "only scanning and importing reach it"


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ArtifactAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    revisions = registry.group(GroupMeta(ArtifactEntityType())).field_group(
        FieldGroupMeta(ArtifactRevisionFieldType()),
        ArtifactRevisionData,
        LookupArtifactRevisionOwnerAction,
        LookupBulkArtifactRevisionOwnerAction,
    )
    return ArtifactAdapter(
        ArtifactProcessors(
            registry.group(GroupMeta(ArtifactEntityType())),
            revisions,
            ArtifactRevisionProcessors(
                registry.group(GroupMeta(ArtifactEntityType())),
                revisions,
                ArtifactRevisionService(
                    ArtifactRepository(engine, provider),
                    OpsRepository(provider),
                    unwired(ArtifactRegistryRepository, _SCANNING),
                    unwired(ObjectStorageRepository, _SCANNING),
                    unwired(VFSStorageRepository, _SCANNING),
                    unwired(StorageNamespaceRepository, _SCANNING),
                    unwired(HuggingFaceRepository, _SCANNING),
                    unwired(ReservoirRegistryRepository, _SCANNING),
                    unwired(VfolderRepository, _SCANNING),
                    unwired(StorageSessionManager, _SCANNING),
                    config,
                    unwired(ValkeyArtifactDownloadTrackingClient, _SCANNING),
                    unwired(BackgroundTaskManager, _SCANNING),
                ),
            ),
            ArtifactService(
                ArtifactRepository(engine, provider),
                unwired(ArtifactRegistryRepository, _SCANNING),
                unwired(ObjectStorageRepository, _SCANNING),
                unwired(VFSStorageRepository, _SCANNING),
                unwired(HuggingFaceRepository, _SCANNING),
                unwired(ReservoirRegistryRepository, _SCANNING),
                unwired(StorageSessionManager, _SCANNING),
                config,
            ),
        )
    )
