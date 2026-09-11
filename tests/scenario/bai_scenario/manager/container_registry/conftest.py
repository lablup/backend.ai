"""The container registry adapter, assembled for one row.

The only place in these scenarios that knows how the adapter is built. It takes two
bundles: its own, and the rbac one behind the allowed-project list. The second is not
decoration — the calls that allow a project on a registry go through it.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.rbac.service import (
    RbacRelationService,
    RbacRoleService,
    RbacRosterService,
)


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ContainerRegistryAdapter:
    provider = V2DBOpsProvider(engine)
    relations = RelationOpsProvider(engine)
    roster = RosterOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return ContainerRegistryAdapter(
        ContainerRegistryProcessors(
            registry.group(GroupMeta(ContainerRegistryEntityType())),
            ContainerRegistryService(engine, ContainerRegistryRepository(engine, relations)),
        ),
        RbacProcessors(
            registry.concern(ConcernMeta(Concern.RBAC)).relation_group(),
            registry.group(GroupMeta(UserEntityType())),
            RbacRelationService(RbacRelationRepository(relations)),
            RbacRosterService(RbacRosterRepository(roster)),
            RbacRoleService(PermissionControllerRepository(engine), RbacRosterRepository(roster)),
            [],
        ),
    )
