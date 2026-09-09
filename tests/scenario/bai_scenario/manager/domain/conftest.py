"""The domain adapter, assembled for one row.

The only place in the domain scenarios that knows how a domain adapter is built. What
it is built with — the config the row overrides, the validators that follow from it,
the recorder — comes from the root conftest.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService


@pytest.fixture
async def adapter(
    engine: Any,
    validators: tuple[ActionValidators, V2ActionValidators],
    monitors: ActionMonitors,
) -> DomainAdapter:
    _, v2_validators = validators
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=v2_validators,
            repository=OpsRepository(provider),
        )
    )
    return DomainAdapter(
        DomainProcessors(
            registry.group(GroupMeta(DomainEntityType())),
            DomainService(DomainRepository(engine, provider)),
            [],
        ),
        ResourceGroupProcessors(
            registry.group(GroupMeta(ResourceGroupEntityType())),
            ResourceGroupService(ResourceGroupRepository(engine, provider)),
        ),
    )
