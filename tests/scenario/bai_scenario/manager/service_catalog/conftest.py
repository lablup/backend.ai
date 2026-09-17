"""The service catalog adapter, assembled for one row.

The one call runs straight against ops, so there is no service to build.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.service_catalog import ServiceCatalogEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.service_catalog.adapter import ServiceCatalogAdapter
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.service_catalog.processors import ServiceCatalogProcessors


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ServiceCatalogAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return ServiceCatalogAdapter(
        ServiceCatalogProcessors(registry.group(GroupMeta(ServiceCatalogEntityType())))
    )
