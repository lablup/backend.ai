"""The entity adapter, assembled for one row.

The adapter lists the entity types the processor wiring names, so each fixture is the
adapter over the wiring that row stands on.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.entity.adapter import EntityAdapter
from ai.backend.manager.api.adapters.entity.types import WiredEntityTypes
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.domain.provider import DomainOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService


def _registry(engine: Any, monitors: ActionMonitors, validators: V2ActionValidators) -> Any:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    return registry


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> EntityAdapter:
    registry = _registry(engine, monitors, validators)
    DomainProcessors(
        registry.group(GroupMeta(DomainEntityType())),
        DomainService(DomainRepository(engine, DomainOpsProvider(engine))),
    )
    return EntityAdapter(WiredEntityTypes(registry))


@pytest.fixture
async def adapter_with_nothing_wired(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> EntityAdapter:
    return EntityAdapter(WiredEntityTypes(_registry(engine, monitors, validators)))
