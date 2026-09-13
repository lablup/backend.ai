"""The runtime variant preset adapter, assembled for one row.

Every call but the update runs against ops. The update reads the stored row first, so it
takes the preset repository beside the ops repository.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.manager.services.runtime_variant_preset.processors import (
    RuntimeVariantPresetProcessors,
)
from ai.backend.manager.services.runtime_variant_preset.service import (
    RuntimeVariantPresetService,
)


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> RuntimeVariantPresetAdapter:
    ops: OpsRepository[Any] = OpsRepository(V2DBOpsProvider(engine))
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(monitors=monitors, validators=validators, repository=ops)
    )
    return RuntimeVariantPresetAdapter(
        RuntimeVariantPresetProcessors(
            registry.group(GroupMeta(RuntimeVariantPresetEntityType())),
            RuntimeVariantPresetService(RuntimeVariantPresetRepository(engine), ops),
        )
    )
