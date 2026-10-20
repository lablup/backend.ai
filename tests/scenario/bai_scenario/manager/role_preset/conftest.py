"""The role preset adapter, assembled for one row.

The only place in the role preset scenarios that knows how a role preset adapter is
built. What it is built with — the validators, the recorder — comes from the root
conftest.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.role_preset import RolePresetEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.role_preset.provider import RolePresetOpsProvider
from ai.backend.manager.repositories.role_preset.repository import RolePresetRepository
from ai.backend.manager.services.role_preset.processors import RolePresetProcessors
from ai.backend.manager.services.role_preset.service import RolePresetService


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> RolePresetAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return RolePresetAdapter(
        RolePresetProcessors(
            registry.group(GroupMeta(RolePresetEntityType())),
            RolePresetService(
                OpsRepository(provider),
                RolePresetRepository(RolePresetOpsProvider(engine)),
            ),
        ),
    )
