"""The runtime variant adapter, assembled for one row. Every call runs against ops."""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.runtime_variant.processors import RuntimeVariantProcessors


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> RuntimeVariantAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    return RuntimeVariantAdapter(
        RuntimeVariantProcessors(registry.group(GroupMeta(RuntimeVariantEntityType())))
    )
