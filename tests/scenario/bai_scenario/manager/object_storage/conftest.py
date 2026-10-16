"""The object storage adapter, assembled for one row.

The presigned URL calls are not in these tables, so their service is a stand-in.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

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
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.artifact.revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
    LookupBulkArtifactRevisionOwnerAction,
)
from ai.backend.manager.services.object_storage.processors import ObjectStorageProcessors
from ai.backend.manager.services.object_storage.service import ObjectStorageService


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ObjectStorageAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    revisions = registry.group(GroupMeta(ArtifactEntityType())).field_group(
        FieldGroupMeta(ArtifactRevisionFieldType()),
        ArtifactRevisionData,
        LookupArtifactRevisionOwnerAction,
        LookupBulkArtifactRevisionOwnerAction,
    )
    return ObjectStorageAdapter(
        ObjectStorageProcessors(
            registry.group(GroupMeta(ObjectStorageEntityType())),
            revisions,
            MagicMock(spec=ObjectStorageService),
        )
    )
