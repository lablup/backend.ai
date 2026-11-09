"""The entity share adapter, assembled for one row.

Every write goes through the share ops and the share repository. Nothing outside the
database is reached.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.entity_share import EntityShareEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.entity_share.adapter import EntityShareAdapter
from ai.backend.manager.repositories.entity_share.repository import EntityShareRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.services.entity_share.processors import EntityShareProcessors
from ai.backend.manager.services.entity_share.service import EntityShareService


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> EntityShareAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return EntityShareAdapter(
        EntityShareProcessors(
            registry.group(GroupMeta(EntityShareEntityType())),
            EntityShareService(EntityShareRepository(ShareOpsProvider(engine))),
        )
    )
