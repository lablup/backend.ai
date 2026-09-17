"""The query preset category adapter, assembled for one row.

Every call of this adapter runs against ops, so there is no service and nothing outside
the database to stand in for.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryEntityType,
)
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.prometheus_query_preset_category.adapter import (
    PrometheusQueryPresetCategoryAdapter,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.prometheus_query_preset_category.processors import (
    PrometheusQueryPresetCategoryProcessors,
)


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> PrometheusQueryPresetCategoryAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return PrometheusQueryPresetCategoryAdapter(
        PrometheusQueryPresetCategoryProcessors(
            registry.group(GroupMeta(PrometheusQueryPresetCategoryEntityType()))
        )
    )
