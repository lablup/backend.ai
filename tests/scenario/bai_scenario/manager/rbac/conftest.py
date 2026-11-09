"""The rbac adapter, assembled for one row.

Role writes and the permission reads these rows exercise run through the permission
controller, so every piece behind them is wired.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.role import RoleEntityType
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
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.permission_contoller.service import PermissionControllerService
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.rbac.service import (
    RbacRelationService,
    RbacRoleService,
    RbacRosterService,
)


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> RBACAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    permission_controller_repository = PermissionControllerRepository(engine)
    roster_repository = RbacRosterRepository(RosterOpsProvider(engine))
    rbac_groups = registry.concern(ConcernMeta(Concern.RBAC))
    rbac = RbacProcessors(
        rbac_groups.relation_group(),
        rbac_groups.group(GroupMeta(UserEntityType())),
        RbacRelationService(RbacRelationRepository(RelationOpsProvider(engine))),
        RbacRosterService(roster_repository),
        RbacRoleService(permission_controller_repository, roster_repository),
    )
    permission_controller = PermissionControllerProcessors(
        rbac_groups.group(GroupMeta(RoleEntityType())),
        rbac_groups.group(GroupMeta(UserEntityType())),
        PermissionControllerService(
            permission_controller_repository,
            RbacPermissionCheckRepository(PermissionOpsProvider(engine), config),
            registry,
        ),
    )
    return RBACAdapter(rbac, permission_controller)
