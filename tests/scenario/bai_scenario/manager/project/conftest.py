"""The project adapter, assembled for one row.

Creating a project and putting somebody on its roster are the two operations these
rows exercise; both answer from the ops path, so the services behind them are wired
and only what a write never reaches is left unwired.
"""

from __future__ import annotations

from typing import Any

import pytest
from bai_scenario.runner.unwired import unwired

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
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
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.project.repositories import ProjectRepositories
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.project.service import ProjectService
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.rbac.service import (
    RbacRelationService,
    RbacRoleService,
    RbacRosterService,
)
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ProjectAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    project_repository = ProjectRepository(
        engine,
        provider,
        config,
        unwired(ValkeyStatClient, "only usage reads reach it"),
        unwired(StorageSessionManager, "only folder work reaches it"),
    )
    project = ProjectProcessors(
        registry.group(GroupMeta(ProjectEntityType())),
        ProjectService(
            unwired(StorageSessionManager, "only folder work reaches it"),
            config,
            unwired(ValkeyStatClient, "only usage reads reach it"),
            ProjectRepositories(project_repository),
        ),
    )
    roster_repository = RbacRosterRepository(RosterOpsProvider(engine))
    rbac_groups = registry.concern(ConcernMeta(Concern.RBAC))
    rbac = RbacProcessors(
        rbac_groups.relation_group(),
        rbac_groups.group(GroupMeta(UserEntityType())),
        RbacRelationService(RbacRelationRepository(RelationOpsProvider(engine))),
        RbacRosterService(roster_repository),
        RbacRoleService(PermissionControllerRepository(engine), roster_repository),
        [],
    )
    domain = DomainProcessors(
        registry.group(GroupMeta(DomainEntityType())),
        DomainService(DomainRepository(engine, provider)),
        [],
    )
    user = UserProcessors(
        registry.group(GroupMeta(UserEntityType())),
        UserService(
            unwired(StorageSessionManager, "only folder work reaches it"),
            unwired(ValkeyStatClient, "only usage reads reach it"),
            unwired(AgentRegistry, "only session work reaches the agents"),
            UserRepository(
                engine,
                provider,
                ShareOpsProvider(engine),
                KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
            ),
            unwired(SchedulingController, "only enqueue schedules"),
        ),
    )
    return ProjectAdapter(project, rbac, domain, user)
