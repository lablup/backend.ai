"""The resource preset adapter, assembled for one row.

The repository reads the config only to check presets, which no table here calls.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_preset.service import ResourcePresetService
from bai_scenario.runner.unwired import unwired


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ResourcePresetAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return ResourcePresetAdapter(
        ResourcePresetProcessors(
            registry.group(GroupMeta(ResourcePresetEntityType())),
            ResourcePresetService(
                ResourcePresetRepository(
                    engine,
                    unwired(ManagerConfigProvider, "프리셋 검사만 설정을 읽는다"),
                    ShareOpsProvider(engine),
                )
            ),
        ),
        ResourceGroupProcessors(
            registry.group(GroupMeta(ResourceGroupEntityType())),
            ResourceGroupService(ResourceGroupRepository(engine, provider)),
        ),
    )
