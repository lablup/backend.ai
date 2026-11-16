"""The object storage adapter, assembled for one row.

The presigned URL calls keep a service, so it is built with the storage proxy faked.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from ai.backend.common.data.entity.artifact import ArtifactEntityType
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionFieldType
from ai.backend.common.data.entity.object_storage import ObjectStorageEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.object_storage.adapter import ObjectStorageAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.storage_namespace.repository import (
    StorageNamespaceRepository,
)
from ai.backend.manager.services.artifact.revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
    LookupBulkArtifactRevisionOwnerAction,
)
from ai.backend.manager.services.object_storage.processors import ObjectStorageProcessors
from ai.backend.manager.services.object_storage.service import ObjectStorageService
from bai_scenario.fakes.storage_proxy import (
    FakeStorageProxyManagerFacingClient,
    FakeStorageSessionManager,
)
from bai_scenario.seeds.object_storage.object_storage import SEEDED_HOST


@pytest.fixture
def storage() -> FakeStorageProxyManagerFacingClient:
    return FakeStorageProxyManagerFacingClient()


@pytest.fixture
def fakes(storage: FakeStorageProxyManagerFacingClient) -> Sequence[object]:
    return (storage,)


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    config: ManagerConfigProvider,
    storage: FakeStorageProxyManagerFacingClient,
) -> ObjectStorageAdapter:
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
    service = ObjectStorageService(
        ArtifactRepository(engine, provider),
        OpsRepository(provider),
        ObjectStorageRepository(engine, provider),
        StorageNamespaceRepository(engine),
        FakeStorageSessionManager({SEEDED_HOST: storage}),
        config,
    )
    return ObjectStorageAdapter(
        ObjectStorageProcessors(
            registry.group(GroupMeta(ObjectStorageEntityType())),
            revisions,
            service,
        )
    )
