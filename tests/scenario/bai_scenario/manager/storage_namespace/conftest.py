"""The storage namespace adapter, assembled for one row.

The domain keeps no service: every operation runs against ops.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.storage_namespace import StorageNamespaceEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.storage_namespace.adapter import StorageNamespaceAdapter
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.storage_namespace.processors import StorageNamespaceProcessors


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> StorageNamespaceAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    return StorageNamespaceAdapter(
        StorageNamespaceProcessors(registry.group(GroupMeta(StorageNamespaceEntityType())))
    )
