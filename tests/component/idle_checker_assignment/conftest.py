"""Component-test fixtures for idle checker assignment v2 endpoints."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.idle_checker import (
    IdleCheckerAssignmentID,
    IdleCheckerEntityType,
    IdleCheckerID,
)
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.data.permission.types import (
    EntityType as LegacyEntityType,
)
from ai.backend.common.data.permission.types import (
    OperationType,
    Permission,
    ScopeType,
)
from ai.backend.common.types import ResourceSlot, SessionTypes
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.bulk.validator.rbac import (
    VirtualEntityAtomicBulkActionRBACValidator,
    VirtualEntityPartialBulkActionRBACValidator,
)
from ai.backend.manager.actions.v2.relation.validator.rbac import (
    VirtualEntityRelationActionRBACValidator,
)
from ai.backend.manager.actions.v2.scope.validator.rbac import (
    VirtualEntityScopeActionRBACValidator,
)
from ai.backend.manager.actions.v2.single_entity.validator.rbac import (
    VirtualEntitySingleEntityActionRBACValidator,
)
from ai.backend.manager.actions.validators.rbac import VirtualEntityRBACValidators
from ai.backend.manager.api.adapters.idle_checker_assignment.adapter import (
    IdleCheckerAssignmentAdapter,
)
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.idle_checker_assignment.handler import (
    V2IdleCheckerAssignmentHandler,
)
from ai.backend.manager.api.rest.v2.idle_checker_assignment.registry import (
    register_v2_idle_checker_assignment_routes,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData, IdleCheckerData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.idle_checker.creators import (
    IdleCheckerAssignmentCreator,
    IdleCheckerCreator,
)
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.ops import DBOpsProvider
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
from ai.backend.manager.services.idle_checker_assignment.service import IdleCheckerAssignmentService
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.rbac.service import (
    RbacRelationService,
    RbacRoleService,
    RbacRosterService,
)

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData, VirtualEntitySeeder


@dataclass
class AssignmentSeedData:
    checker_id: IdleCheckerID
    domain_id: DomainID
    project_id: ProjectID
    other_project_id: ProjectID
    domain_assignment_id: IdleCheckerAssignmentID
    project_assignment_id: IdleCheckerAssignmentID
    other_project_assignment_id: IdleCheckerAssignmentID
    user_assignment_id: IdleCheckerAssignmentID


async def _provision(conn: sa.ext.asyncio.AsyncConnection, scope: EntityIdentifier) -> None:
    """The node a create writes for a scope: it owns and governs itself."""
    node_id = uuid.uuid4()
    await conn.execute(
        sa.insert(VirtualEntityRow.__table__).values(
            id=node_id, entity_type=scope.entity_type(), entity_id=scope
        )
    )
    await conn.execute(
        sa.insert(EntityMembershipRow.__table__).values(
            virtual_entity_id=node_id, member_entity_id=node_id, capped=False
        )
    )
    await conn.execute(
        sa.insert(ScopeBindingRow.__table__).values(
            virtual_entity_id=node_id, scope_entity_id=node_id, permission_cap=None
        )
    )


async def _teardown(conn: sa.ext.asyncio.AsyncConnection, scope: EntityIdentifier) -> None:
    await conn.execute(
        VirtualEntityRow.__table__.delete().where(
            VirtualEntityRow.__table__.c.entity_type == scope.entity_type(),
            VirtualEntityRow.__table__.c.entity_id == scope,
        )
    )


@pytest.fixture()
def action_registry(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> ProcessorRegistry[Any]:
    """One registry for every processor these tests wire, with real RBAC validators
    against the real DB."""
    permission_repo = PermissionControllerRepository(database_engine)
    validators = VirtualEntityRBACValidators(
        scope=VirtualEntityScopeActionRBACValidator(permission_repo, config_provider),
        single_entity=VirtualEntitySingleEntityActionRBACValidator(
            permission_repo, config_provider
        ),
        partial_bulk=VirtualEntityPartialBulkActionRBACValidator(permission_repo, config_provider),
        atomic_bulk=VirtualEntityAtomicBulkActionRBACValidator(permission_repo, config_provider),
        relation=VirtualEntityRelationActionRBACValidator(permission_repo, config_provider),
    )
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=validators.to_action_validators(),
            repository=OpsRepository(V2DBOpsProvider(database_engine)),
        )
    )


@pytest.fixture()
def idle_checker_assignment_processors(
    database_engine: ExtendedAsyncSAEngine,
    action_registry: ProcessorRegistry[Any],
) -> IdleCheckerAssignmentProcessors:
    """The binding reads; its writes are the rbac boundary's."""
    service = IdleCheckerAssignmentService(
        IdleCheckerRepository(DBOpsProvider(database_engine), RelationOpsProvider(database_engine))
    )
    groups = action_registry.concern(ConcernMeta(Concern.SESSION))
    return IdleCheckerAssignmentProcessors(
        groups.group(GroupMeta(IdleCheckerEntityType())),
        service,
    )


@pytest.fixture()
def rbac_processors(
    database_engine: ExtendedAsyncSAEngine,
    action_registry: ProcessorRegistry[Any],
) -> RbacProcessors:
    """The relation writes a binding change runs, checked against both its scopes."""
    rbac_groups = action_registry.concern(ConcernMeta(Concern.RBAC))
    return RbacProcessors(
        rbac_groups.relation_group(),
        rbac_groups.group(GroupMeta(UserEntityType())),
        RbacRelationService(RbacRelationRepository(RelationOpsProvider(database_engine))),
        RbacRosterService(RbacRosterRepository(RosterOpsProvider(database_engine))),
        RbacRoleService(
            PermissionControllerRepository(database_engine),
            RbacRosterRepository(RosterOpsProvider(database_engine)),
        ),
        [],
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    idle_checker_assignment_processors: IdleCheckerAssignmentProcessors,
    rbac_processors: RbacProcessors,
) -> list[RouteRegistry]:
    """Register v2 idle checker assignment routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.idle_checker_assignment = idle_checker_assignment_processors
    processors.rbac = rbac_processors
    handler = V2IdleCheckerAssignmentHandler(
        adapter=IdleCheckerAssignmentAdapter(processors.idle_checker_assignment, processors.rbac)
    )
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_idle_checker_assignment_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """V2 client registry authenticated as superadmin."""
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """V2 client registry authenticated as a regular (non-admin) user."""
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def assignment_seed(
    database_engine: ExtendedAsyncSAEngine,
    database_fixture: None,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[AssignmentSeedData]:
    """Seed a domain and two projects, one checker, and one assignment per scope.

    Each scope gets the node a create would have written; the checker is created the
    way the catalog creates it; each assignment is linked through the repository.
    """
    domain_id = DomainID(uuid.uuid4())
    project_id = ProjectID(uuid.uuid4())
    other_project_id = ProjectID(uuid.uuid4())
    domain_name = f"icb-domain-{domain_id.hex[:8]}"
    policy_name = f"icb-prp-{project_id.hex[:8]}"
    async with database_engine.begin_session() as db_sess:
        db_sess.add(DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot()))
        db_sess.add(
            ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=0,
            )
        )
        await db_sess.flush()
        db_sess.add(
            ProjectRow(
                id=project_id,
                name=f"icb-project-{project_id.hex[:8]}",
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy=policy_name,
            )
        )
        db_sess.add(
            ProjectRow(
                id=other_project_id,
                name=f"icb-project-{other_project_id.hex[:8]}",
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy=policy_name,
            )
        )
    provisioned: list[EntityIdentifier] = [domain_id, project_id, other_project_id]
    async with database_engine.begin() as conn:
        for scope in provisioned:
            await _provision(conn, scope)
    catalog: OpsRepository[IdleCheckerData] = OpsRepository(V2DBOpsProvider(database_engine))
    checker = await catalog.create_global_entity(
        IdleCheckerCreator(
            name=f"icb-checker-{domain_id.hex[:8]}",
            description=None,
            target_session_types=[SessionTypes.INTERACTIVE],
            initial_grace_period_seconds=0,
            spec=IdleCheckerSpec(
                type=CheckerType.SESSION_LIFETIME,
                session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
            ),
        )
    )
    checker_id = checker.id
    repository = IdleCheckerRepository(
        DBOpsProvider(database_engine), RelationOpsProvider(database_engine)
    )
    relations = RbacRelationRepository(RelationOpsProvider(database_engine))
    assignments: list[IdleCheckerAssignmentData] = []
    for scope in [*provisioned, regular_user_fixture.user_uuid]:
        await relations.create([(scope, checker_id)], IdleCheckerAssignmentCreator(enabled=True))
        assignments.append(await repository.get_assignment_by_pair(scope, checker_id))
    seed = AssignmentSeedData(
        checker_id=checker_id,
        domain_id=domain_id,
        project_id=project_id,
        other_project_id=other_project_id,
        domain_assignment_id=assignments[0].id,
        project_assignment_id=assignments[1].id,
        other_project_assignment_id=assignments[2].id,
        user_assignment_id=assignments[3].id,
    )
    yield seed
    async with database_engine.begin() as conn:
        await _teardown(conn, checker_id)
        for scope in provisioned:
            await _teardown(conn, scope)
        # Assignments are removed by the checker FK cascade.
        await conn.execute(
            IdleCheckerRow.__table__.delete().where(IdleCheckerRow.__table__.c.id == checker_id)
        )
        await conn.execute(
            ProjectRow.__table__.delete().where(
                ProjectRow.__table__.c.id.in_([project_id, other_project_id])
            )
        )
        await conn.execute(
            ProjectResourcePolicyRow.__table__.delete().where(
                ProjectResourcePolicyRow.__table__.c.name == policy_name
            )
        )
        await conn.execute(
            DomainRow.__table__.delete().where(DomainRow.__table__.c.id == domain_id)
        )


async def _grant(
    database_engine: ExtendedAsyncSAEngine,
    user_id: UserID,
    scope_type: str,
    scope_id: uuid.UUID,
    entity_type: str,
    operations: tuple[OperationType, ...],
) -> AsyncIterator[None]:
    role_id = uuid.uuid4()
    async with database_engine.begin_session() as db_sess:
        db_sess.add(
            RoleRow(
                id=role_id,
                name=f"icb-role-{role_id.hex[:8]}",
                description="idle checker assignment component test role",
                scope_type=EntityType(scope_type),
                scope_id=scope_id,
            )
        )
        await db_sess.flush()
        db_sess.add(UserRoleRow(user_id=user_id, role_id=role_id))
        for operation in operations:
            db_sess.add(
                PermissionRow(
                    role_id=role_id,
                    scope_type=scope_type,
                    scope_id=str(scope_id),
                    entity_type=entity_type,
                    permission=Permission.from_operation(operation),
                )
            )
        await db_sess.flush()
    yield
    async with database_engine.begin() as conn:
        await conn.execute(
            PermissionRow.__table__.delete().where(PermissionRow.__table__.c.role_id == role_id)
        )
        await conn.execute(
            UserRoleRow.__table__.delete().where(UserRoleRow.__table__.c.role_id == role_id)
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id == role_id))


@pytest.fixture()
async def project_assignment_read_permission(
    database_engine: ExtendedAsyncSAEngine,
    regular_user_fixture: UserFixtureData,
    assignment_seed: AssignmentSeedData,
) -> AsyncIterator[None]:
    """Grant the regular user READ on idle checkers within the seeded project: what
    the project's bindings reach, and what resolving one of them costs."""
    async for _ in _grant(
        database_engine,
        regular_user_fixture.user_uuid,
        ScopeType.PROJECT,
        assignment_seed.project_id,
        IdleCheckerEntityType(),
        (OperationType.READ,),
    ):
        yield


@pytest.fixture()
async def project_assignment_manage_permission(
    database_engine: ExtendedAsyncSAEngine,
    regular_user_fixture: UserFixtureData,
    assignment_seed: AssignmentSeedData,
) -> AsyncIterator[None]:
    """Grant the regular user what switching or unlinking the seeded project's binding
    costs: the relation is answered for by both sides, so the grant names the project
    and the checker, each as itself. READ on idle checkers within the project pays for
    the id resolution.
    """
    async for _ in _grant(
        database_engine,
        regular_user_fixture.user_uuid,
        ScopeType.PROJECT,
        assignment_seed.project_id,
        LegacyEntityType.PROJECT,
        (OperationType.SOFT_DELETE, OperationType.HARD_DELETE),
    ):
        async for _ in _grant(
            database_engine,
            regular_user_fixture.user_uuid,
            ScopeType.PROJECT,
            assignment_seed.project_id,
            IdleCheckerEntityType(),
            (OperationType.READ,),
        ):
            async for _ in _grant(
                database_engine,
                regular_user_fixture.user_uuid,
                IdleCheckerEntityType(),
                assignment_seed.checker_id,
                IdleCheckerEntityType(),
                (OperationType.SOFT_DELETE, OperationType.HARD_DELETE),
            ):
                yield


@pytest.fixture()
async def user_self_scope_permission(
    database_engine: ExtendedAsyncSAEngine,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[None]:
    """Grant the regular user everything on entity type USER at their own user scope,
    and READ on the idle checkers bound to them.

    This mirrors what a user's system self-role carries. Owning one side of the
    relation is not enough: the checker answers for it too.
    """
    async for _ in _grant(
        database_engine,
        regular_user_fixture.user_uuid,
        ScopeType.USER,
        regular_user_fixture.user_uuid,
        LegacyEntityType.USER,
        (
            OperationType.READ,
            OperationType.UPDATE,
            OperationType.SOFT_DELETE,
            OperationType.HARD_DELETE,
        ),
    ):
        async for _ in _grant(
            database_engine,
            regular_user_fixture.user_uuid,
            ScopeType.USER,
            regular_user_fixture.user_uuid,
            IdleCheckerEntityType(),
            (OperationType.READ,),
        ):
            yield


@pytest.fixture()
async def user_in_seeded_project(
    database_engine: ExtendedAsyncSAEngine,
    regular_user_fixture: UserFixtureData,
    assignment_seed: AssignmentSeedData,
    virtual_entity_seeder: VirtualEntitySeeder,
) -> AsyncIterator[None]:
    """Enroll the regular user in the seeded project."""
    async with database_engine.begin() as conn:
        await virtual_entity_seeder.enroll_user_in_project(
            conn, assignment_seed.project_id, regular_user_fixture.user_uuid
        )
    yield
    async with database_engine.begin() as conn:
        project_node = sa.select(VirtualEntityRow.__table__.c.id).where(
            VirtualEntityRow.__table__.c.entity_type == ScopeType.PROJECT,
            VirtualEntityRow.__table__.c.entity_id == assignment_seed.project_id,
        )
        user_node = sa.select(VirtualEntityRow.__table__.c.id).where(
            VirtualEntityRow.__table__.c.entity_type == ScopeType.USER,
            VirtualEntityRow.__table__.c.entity_id == regular_user_fixture.user_uuid,
        )
        await conn.execute(
            EntityMembershipRow.__table__.delete().where(
                EntityMembershipRow.__table__.c.virtual_entity_id == project_node.scalar_subquery(),
                EntityMembershipRow.__table__.c.member_entity_id == user_node.scalar_subquery(),
            )
        )
