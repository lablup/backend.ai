"""The domain adapter, assembled for one row.

The only place in the domain scenarios that knows how a domain adapter is built. What
it is built with — the config the row overrides, the validators that follow from it,
the recorder — comes from the root conftest.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.monitors.action_monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.domain.provider import DomainOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
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
) -> DomainAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    domain = DomainProcessors(
        registry.group(GroupMeta(DomainEntityType())),
        registry.concern(ConcernMeta(Concern.ORGANIZATION)).relation_group(),
        registry.group(GroupMeta(ContainerRegistryEntityType())),
        DomainService(DomainRepository(engine, DomainOpsProvider(engine))),
    )
    rbac_groups = registry.concern(ConcernMeta(Concern.RBAC))
    roster = RosterOpsProvider(engine)
    rbac = RbacProcessors(
        rbac_groups.relation_group(),
        rbac_groups.group(GroupMeta(UserEntityType())),
        RbacRelationService(RbacRelationRepository(RelationOpsProvider(engine))),
        RbacRosterService(RbacRosterRepository(roster)),
        RbacRoleService(PermissionControllerRepository(engine), RbacRosterRepository(roster)),
    )
    return DomainAdapter(domain, rbac)
