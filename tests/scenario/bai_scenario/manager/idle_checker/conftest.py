"""The idle checker adapter, assembled for one row.

The purge the tables call runs straight against ops, so the service's repositories
stay unwired.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.idle_checker.adapter import IdleCheckerAdapter
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.services.idle_checker.processors import IdleCheckerProcessors
from ai.backend.manager.services.idle_checker.service import IdleCheckerService
from bai_scenario.runner.unwired import unwired


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> IdleCheckerAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return IdleCheckerAdapter(
        IdleCheckerProcessors(
            registry.group(GroupMeta(IdleCheckerEntityType())),
            registry.group(GroupMeta(SessionEntityType())),
            IdleCheckerService(
                unwired(IdleCheckerRepository, "only create and update reach it"),
                unwired(PrometheusQueryPresetRepository, "only utilization checks reach it"),
                OpsRepository(provider),
            ),
        )
    )
