"""The Reservoir registry adapter, assembled for one row.

Single update and purge go through the service behind a per-registry check; the partial
bulk calls go through the service behind a check per named registry.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.reservoir_registry.adapter import (
    ReservoirRegistryAdapter,
)
from ai.backend.manager.repositories.artifact_registry.repository import (
    ArtifactRegistryRepository,
)
from ai.backend.manager.repositories.huggingface_registry.repository import (
    HuggingFaceRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.artifact_registry.provider import (
    ArtifactRegistryOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors
from ai.backend.manager.services.artifact_registry.service import ArtifactRegistryService


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ReservoirRegistryAdapter:
    provider = V2DBOpsProvider(engine)
    registry_ops = ArtifactRegistryOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    service = ArtifactRegistryService(
        HuggingFaceRepository(engine, registry_ops),
        ReservoirRegistryRepository(engine, registry_ops),
        ArtifactRegistryRepository(engine, provider),
    )
    return ReservoirRegistryAdapter(
        ArtifactRegistryProcessors(
            registry.group(GroupMeta(ArtifactRegistryEntityType())),
            registry.group(GroupMeta(ArtifactRegistryEntityType())),
            registry.group(GroupMeta(ArtifactRegistryEntityType())),
            service,
        )
    )
