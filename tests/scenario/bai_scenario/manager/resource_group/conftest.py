"""The resource group adapter, assembled for one row.

Making a resource group and reading one back are what these rows exercise; the two
coordinators only long-running work reaches are left unwired.
"""

from __future__ import annotations

from typing import Any

import pytest
from bai_scenario.runner.unwired import unwired

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
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
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.rbac.service import (
    RbacRelationService,
    RbacRoleService,
    RbacRosterService,
)
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator


@pytest.fixture
async def adapter(
    engine: Any,
    validators: tuple[ActionValidators, V2ActionValidators],
    monitors: ActionMonitors,
) -> ResourceGroupAdapter:
    _, v2_validators = validators
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=v2_validators,
            repository=OpsRepository(provider),
        )
    )
    roster_repository = RbacRosterRepository(RosterOpsProvider(engine))
    rbac_groups = registry.concern(ConcernMeta(Concern.RBAC))
    return ResourceGroupAdapter(
        ResourceGroupProcessors(
            registry.group(GroupMeta(ResourceGroupEntityType())),
            ResourceGroupService(ResourceGroupRepository(engine, provider)),
        ),
        RbacProcessors(
            rbac_groups.relation_group(),
            rbac_groups.group(GroupMeta(UserEntityType())),
            RbacRelationService(RbacRelationRepository(RelationOpsProvider(engine))),
            RbacRosterService(roster_repository),
            RbacRoleService(PermissionControllerRepository(engine), roster_repository),
            [],
        ),
        DomainProcessors(
            registry.group(GroupMeta(DomainEntityType())),
            DomainService(DomainRepository(engine, provider)),
            [],
        ),
        unwired(DeploymentCoordinator, "only deployment work reaches it"),
        unwired(ScheduleCoordinator, "only scheduling reaches it"),
    )
