"""The resource group adapter, assembled for one row.

The two coordinators are asked only which handlers are registered, when the default
options are replaced; each is a fake answering with the handlers it was built from.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

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
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
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
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
)
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.handlers.base import DeploymentHandler
from ai.backend.manager.sokovan.deployment.handlers.replica import CheckReplicaDeploymentHandler
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.terminate_sessions import (
    TerminateSessionsLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator
from bai_scenario.fakes.deployment import FakeDeploymentCoordinator
from bai_scenario.fakes.scheduler import FakeScheduleCoordinator
from bai_scenario.runner.unwired import unwired


@pytest.fixture
def deployment_handlers() -> Sequence[DeploymentHandler]:
    """등록된 배포 처리기. 이름만 읽으므로 안쪽은 배선하지 않는다."""
    return (
        CheckReplicaDeploymentHandler(
            deployment_executor=unwired(DeploymentExecutor, "처리기의 이름만 읽는다"),
            deployment_controller=unwired(DeploymentController, "처리기의 이름만 읽는다"),
        ),
    )


@pytest.fixture
def lifecycle_handlers() -> Sequence[SessionLifecycleHandler]:
    """등록된 세션 처리기. 이름만 읽으므로 안쪽은 배선하지 않는다."""
    return (
        TerminateSessionsLifecycleHandler(
            terminator=unwired(SessionTerminator, "처리기의 이름만 읽는다"),
            repository=unwired(SchedulerRepository, "처리기의 이름만 읽는다"),
        ),
    )


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    deployment_handlers: Sequence[DeploymentHandler],
    lifecycle_handlers: Sequence[SessionLifecycleHandler],
) -> ResourceGroupAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
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
        ),
        DomainProcessors(
            registry.group(GroupMeta(DomainEntityType())),
            DomainService(DomainRepository(engine, RelationOpsProvider(engine))),
        ),
        FakeDeploymentCoordinator(deployment_handlers),
        FakeScheduleCoordinator(lifecycle_handlers),
    )
