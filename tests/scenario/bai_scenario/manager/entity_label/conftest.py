"""The entity label adapter, assembled for one row.

The only place in the entity label scenarios that knows how the adapter is built. The
domain operations are wired beside it so `domain` is an entity type a label may name.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.entity_label import EntityLabelFieldType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.entity.types import WiredEntityTypes
from ai.backend.manager.api.adapters.entity_label.adapter import EntityLabelAdapter
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.domain.provider import DomainOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.entity_label.actions.lookup_owner import (
    LookupBulkEntityLabelOwnerAction,
    LookupEntityLabelOwnerAction,
)
from ai.backend.manager.services.entity_label.processors import EntityLabelProcessors


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> EntityLabelAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    DomainProcessors(
        registry.group(GroupMeta(DomainEntityType())),
        DomainService(DomainRepository(engine, DomainOpsProvider(engine))),
    )
    processors = EntityLabelProcessors(
        registry.dangling_lookup_field_group(
            FieldGroupMeta(EntityLabelFieldType()),
            EntityLabelData,
            LookupEntityLabelOwnerAction,
            LookupBulkEntityLabelOwnerAction,
        )
    )
    return EntityLabelAdapter(processors, WiredEntityTypes(registry))
