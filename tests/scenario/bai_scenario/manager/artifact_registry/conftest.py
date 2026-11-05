"""The artifact registry adapter, assembled for one row.

A registry read goes through a per-registry check, and the batch reads answer for each
registry. Only the meta reads are wired; the per-type registry repositories are here
because the service takes them.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.artifact_registry.adapter import ArtifactRegistryAdapter
from ai.backend.manager.repositories.artifact_registry.repository import (
    ArtifactRegistryRepository,
)
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors
from ai.backend.manager.services.artifact_registry.service import ArtifactRegistryService
from bai_scenario.runner.unwired import unwired

_SCANNING = "only the meta reads are wired"


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ArtifactRegistryAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return ArtifactRegistryAdapter(
        ArtifactRegistryProcessors(
            registry.group(GroupMeta(ArtifactRegistryEntityType())),
            registry.group(GroupMeta(ArtifactRegistryEntityType())),
            registry.group(GroupMeta(ArtifactRegistryEntityType())),
            ArtifactRegistryService(
                unwired(HuggingFaceRepository, _SCANNING),
                unwired(ReservoirRegistryRepository, _SCANNING),
                ArtifactRegistryRepository(engine, provider),
            ),
        )
    )
