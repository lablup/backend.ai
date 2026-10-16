"""The idle checker assignment adapter, assembled for one row.

An assignment is a relation, so its writes go through the RBAC relation processors.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType
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
from ai.backend.manager.api.adapters.idle_checker_assignment.adapter import (
    IdleCheckerAssignmentAdapter,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.services.idle_checker_assignment.processors import (
    IdleCheckerAssignmentProcessors,
)
from ai.backend.manager.services.idle_checker_assignment.service import (
    IdleCheckerAssignmentService,
)
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.rbac.service import (
    RbacRelationService,
    RbacRoleService,
    RbacRosterService,
)


@pytest.fixture
async def adapter(
    engine: ExtendedAsyncSAEngine,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> IdleCheckerAssignmentAdapter:
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
    rbac_groups = registry.concern(ConcernMeta(Concern.RBAC))
    return IdleCheckerAssignmentAdapter(
        IdleCheckerAssignmentProcessors(
            registry.group(GroupMeta(IdleCheckerEntityType())),
            IdleCheckerAssignmentService(IdleCheckerRepository(engine, relations, provider)),
        ),
        RbacProcessors(
            rbac_groups.relation_group(),
            rbac_groups.group(GroupMeta(UserEntityType())),
            RbacRelationService(RbacRelationRepository(relations)),
            RbacRosterService(RbacRosterRepository(roster)),
            RbacRoleService(PermissionControllerRepository(engine), RbacRosterRepository(roster)),
        ),
    )
