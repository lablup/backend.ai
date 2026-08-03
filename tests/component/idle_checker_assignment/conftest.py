"""Component-test fixtures for idle checker assignment v2 endpoints."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    Permission,
    RelationType,
    ScopeType,
)
from ai.backend.common.types import ResourceSlot, SessionTypes
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.bulk import BulkActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
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
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.idle_checker_assignment.processors import (
    IdleCheckerAssignmentProcessors,
)
from ai.backend.manager.services.idle_checker_assignment.service import IdleCheckerAssignmentService
from ai.backend.manager.services.processors import Processors
from ai.backend.testutils.action_validators import mock_virtual_scope_rbac_validators

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData


@dataclass
class AssignmentSeedData:
    domain_id: uuid.UUID
    project_id: uuid.UUID
    other_project_id: uuid.UUID
    domain_assignment_id: uuid.UUID
    project_assignment_id: uuid.UUID
    other_project_assignment_id: uuid.UUID


@pytest.fixture()
def idle_checker_assignment_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> IdleCheckerAssignmentProcessors:
    """Assignment processors with real RBAC validators against the real DB."""
    service = IdleCheckerAssignmentService(IdleCheckerRepository(DBOpsProvider(database_engine)))
    permission_repo = PermissionControllerRepository(database_engine)
    return IdleCheckerAssignmentProcessors(
        service=service,
        action_monitors=[],
        validators=ActionValidators(
            rbac=RBACValidators(
                scope=AsyncMock(),
                single_entity=SingleEntityActionRBACValidator(permission_repo, MagicMock()),
                bulk=BulkActionRBACValidator(permission_repo, MagicMock()),
            ),
            virtual_scope_rbac=mock_virtual_scope_rbac_validators(),
        ),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    idle_checker_assignment_processors: IdleCheckerAssignmentProcessors,
) -> list[RouteRegistry]:
    """Register v2 idle checker assignment routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.idle_checker_assignment = idle_checker_assignment_processors
    handler = V2IdleCheckerAssignmentHandler(adapter=IdleCheckerAssignmentAdapter(processors))
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
) -> AsyncIterator[AssignmentSeedData]:
    """Seed a domain and two projects, one checker, and one assignment per scope.

    The assignments model super-admin-created rows; each also gets its RBAC scope
    association row so that single-entity scope-chain checks can resolve the
    assignment back to its scope.
    """
    domain_id = uuid.uuid4()
    project_id = uuid.uuid4()
    other_project_id = uuid.uuid4()
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
            GroupRow(
                id=project_id,
                name=f"icb-project-{project_id.hex[:8]}",
                domain_name=domain_name,
                domain_id=domain_id,
                total_resource_slots=ResourceSlot(),
                resource_policy=policy_name,
            )
        )
        db_sess.add(
            GroupRow(
                id=other_project_id,
                name=f"icb-project-{other_project_id.hex[:8]}",
                domain_name=domain_name,
                domain_id=domain_id,
                total_resource_slots=ResourceSlot(),
                resource_policy=policy_name,
            )
        )
        checker = IdleCheckerRow(
            name=f"icb-checker-{domain_id.hex[:8]}",
            description=None,
            target_session_types=[SessionTypes.INTERACTIVE],
            initial_grace_period_seconds=0,
            spec=IdleCheckerSpec(
                type=CheckerType.SESSION_LIFETIME,
                session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
            ),
        )
        db_sess.add(checker)
        await db_sess.flush()
        checker_id = checker.id
        domain_assignment = IdleCheckerBindingRow(
            scope_type=ScopeType.DOMAIN,
            scope_id=domain_id,
            idle_checker_id=checker_id,
            enabled=True,
        )
        project_assignment = IdleCheckerBindingRow(
            scope_type=ScopeType.PROJECT,
            scope_id=project_id,
            idle_checker_id=checker_id,
            enabled=True,
        )
        other_project_assignment = IdleCheckerBindingRow(
            scope_type=ScopeType.PROJECT,
            scope_id=other_project_id,
            idle_checker_id=checker_id,
            enabled=True,
        )
        db_sess.add(domain_assignment)
        db_sess.add(project_assignment)
        db_sess.add(other_project_assignment)
        await db_sess.flush()
        assignment_scopes = [
            (domain_assignment.id, ScopeType.DOMAIN, str(domain_id)),
            (project_assignment.id, ScopeType.PROJECT, str(project_id)),
            (other_project_assignment.id, ScopeType.PROJECT, str(other_project_id)),
        ]
        for assignment_id, scope_type, scope_id in assignment_scopes:
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=scope_type,
                    scope_id=scope_id,
                    entity_type=EntityType.IDLE_CHECKER_ASSIGNMENT,
                    entity_id=str(assignment_id),
                    relation_type=RelationType.AUTO,
                )
            )
        await db_sess.flush()
        seed = AssignmentSeedData(
            domain_id=domain_id,
            project_id=project_id,
            other_project_id=other_project_id,
            domain_assignment_id=domain_assignment.id,
            project_assignment_id=project_assignment.id,
            other_project_assignment_id=other_project_assignment.id,
        )
    yield seed
    async with database_engine.begin() as conn:
        # Assignments are removed by the checker FK cascade.
        await conn.execute(
            AssociationScopesEntitiesRow.__table__.delete().where(
                AssociationScopesEntitiesRow.__table__.c.entity_id.in_([
                    str(seed.domain_assignment_id),
                    str(seed.project_assignment_id),
                    str(seed.other_project_assignment_id),
                ])
            )
        )
        await conn.execute(
            IdleCheckerRow.__table__.delete().where(IdleCheckerRow.__table__.c.id == checker_id)
        )
        await conn.execute(
            GroupRow.__table__.delete().where(
                GroupRow.__table__.c.id.in_([project_id, other_project_id])
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


@pytest.fixture()
async def project_read_permission(
    database_engine: ExtendedAsyncSAEngine,
    regular_user_fixture: UserFixtureData,
    assignment_seed: AssignmentSeedData,
) -> AsyncIterator[None]:
    """Grant the regular user PROJECT:READ on the seeded project (self-scope)."""
    role_id = uuid.uuid4()
    async with database_engine.begin_session() as db_sess:
        db_sess.add(
            RoleRow(
                id=role_id,
                name=f"icb-role-{role_id.hex[:8]}",
                description="idle checker assignment component test role",
            )
        )
        await db_sess.flush()
        db_sess.add(UserRoleRow(user_id=regular_user_fixture.user_uuid, role_id=role_id))
        db_sess.add(
            PermissionRow(
                role_id=role_id,
                scope_type=ScopeType.PROJECT,
                scope_id=str(assignment_seed.project_id),
                entity_type=EntityType.PROJECT,
                operation=OperationType.READ,
                permission=Permission.from_operation(OperationType.READ),
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
async def project_assignment_manage_permission(
    database_engine: ExtendedAsyncSAEngine,
    regular_user_fixture: UserFixtureData,
    assignment_seed: AssignmentSeedData,
) -> AsyncIterator[None]:
    """Grant the regular user UPDATE/PURGE on idle checker assignments of the seeded project.

    Permissions are attached at the PROJECT scope with subject entity type
    ``IDLE_CHECKER_ASSIGNMENT``, so they apply to assignments resolved to that project
    via the scope chain — not to assignments of any other scope.
    """
    role_id = uuid.uuid4()
    async with database_engine.begin_session() as db_sess:
        db_sess.add(
            RoleRow(
                id=role_id,
                name=f"icb-manage-role-{role_id.hex[:8]}",
                description="idle checker assignment manage test role",
            )
        )
        await db_sess.flush()
        db_sess.add(UserRoleRow(user_id=regular_user_fixture.user_uuid, role_id=role_id))
        for operation in (OperationType.UPDATE, OperationType.HARD_DELETE):
            db_sess.add(
                PermissionRow(
                    role_id=role_id,
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(assignment_seed.project_id),
                    entity_type=EntityType.IDLE_CHECKER_ASSIGNMENT,
                    operation=operation,
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
