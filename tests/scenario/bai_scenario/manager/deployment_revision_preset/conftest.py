"""The deployment revision preset adapter, assembled for one row.

An update restates the preset's slots, so it goes through the preset service; the rest
runs against ops.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentPresetRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.deployment_revision_preset.processors import (
    DeploymentPresetProcessors,
)
from ai.backend.manager.services.deployment_revision_preset.service import (
    DeploymentPresetService,
)


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> DeploymentRevisionPresetAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors, validators=validators, repository=OpsRepository(provider)
        )
    )
    return DeploymentRevisionPresetAdapter(
        DeploymentPresetProcessors(
            registry.group(GroupMeta(DeploymentPresetEntityType())),
            DeploymentPresetService(DeploymentPresetRepository(provider)),
        )
    )
