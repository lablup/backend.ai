"""Component test fixtures for v2 Session GET endpoint with RBAC validation."""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
import yarl
from dateutil.tz import tzutc

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RelationType,
    RoleStatus,
    ScopeType,
)
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.common.types import ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.bulk import BulkActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.session.handler import V2SessionHandler
from ai.backend.manager.api.rest.v2.session.registry import register_v2_session_routes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
    from tests.component.conftest import ServerInfo, UserFixtureData


@dataclass
class SessionSeedData:
    session_id: SessionId
    session_name: str
    kernel_id: uuid.UUID
    access_key: str
    domain_name: str
    user_uuid: uuid.UUID | None = None


@pytest.fixture()
def rbac_permission_repo(
    database_engine: ExtendedAsyncSAEngine,
) -> PermissionControllerRepository:
    """Real permission controller repository backed by real DB."""
    return PermissionControllerRepository(database_engine)


@pytest.fixture()
def session_repository(
    database_engine: ExtendedAsyncSAEngine,
) -> SessionRepository:
    return SessionRepository(database_engine)


@pytest.fixture()
def scheduling_controller_mock() -> AsyncMock:
    """Mock scheduling controller. Tests can override `mark_sessions_for_termination`
    to return a custom `MarkTerminatingResult`.
    """
    return AsyncMock()


@pytest.fixture()
async def session_processors(
    session_repository: SessionRepository,
    background_task_manager: BackgroundTaskManager,
    error_monitor: ErrorPluginContext,
    rbac_permission_repo: PermissionControllerRepository,
    scheduling_controller_mock: AsyncMock,
) -> SessionProcessors:
    """SessionProcessors with real SingleEntityActionRBACValidator.

    RBAC checks use check_permission_with_scope_chain() against the real DB.
    """
    args = SessionServiceArgs(
        agent_registry=AsyncMock(),
        event_fetcher=AsyncMock(),
        background_task_manager=background_task_manager,
        event_hub=AsyncMock(),
        error_monitor=error_monitor,
        idle_checker_host=AsyncMock(),
        session_repository=session_repository,
        scheduler_repository=AsyncMock(),
        scheduling_controller=scheduling_controller_mock,
        appproxy_client_pool=AsyncMock(),
        user_repository=AsyncMock(),
    )
    service = SessionService(args)
    real_single_entity_validator = SingleEntityActionRBACValidator(
        rbac_permission_repo, MagicMock()
    )
    real_bulk_validator = BulkActionRBACValidator(rbac_permission_repo, MagicMock())
    return SessionProcessors(
        service=service,
        action_monitors=[],
        validators=ActionValidators(
            rbac=RBACValidators(
                scope=AsyncMock(),
                single_entity=real_single_entity_validator,
                bulk=real_bulk_validator,
            )
        ),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    session_processors: SessionProcessors,
) -> list[RouteRegistry]:
    """Register v2 session routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.session = session_processors
    adapter = SessionAdapter(processors)
    handler = V2SessionHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_session_routes(handler, route_deps))
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


# ---------------------------------------------------------------------------
# RBAC setup: user system role with owner permissions
# ---------------------------------------------------------------------------


@pytest.fixture()
async def user_system_role(
    db_engine: SAEngine,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[uuid.UUID]:
    """Create a system role with owner permissions for the regular user.

    Replicates what the RoleManager does at user creation time:
    RoleRow + UserRoleRow + PermissionRows for owner-accessible entity types.
    """
    role_id = uuid.uuid4()
    user_uuid = regular_user_fixture.user_uuid

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name=f"user-{str(user_uuid)[:8]}",
                status=RoleStatus.ACTIVE,
            )
        )
        await conn.execute(
            sa.insert(UserRoleRow.__table__).values(
                user_id=user_uuid,
                role_id=role_id,
            )
        )
        # Scope the role to the user
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__).values(
                scope_type=ScopeType.USER,
                scope_id=str(user_uuid),
                entity_type=EntityType.ROLE,
                entity_id=str(role_id),
                relation_type=RelationType.AUTO,
            )
        )
        # Grant owner permissions for all owner-accessible entity types in user scope
        for entity_type in EntityType.owner_accessible_entity_types_in_user():
            for operation in OperationType.owner_operations():
                await conn.execute(
                    sa.insert(PermissionRow.__table__).values(
                        role_id=role_id,
                        scope_type=ScopeType.USER,
                        scope_id=str(user_uuid),
                        entity_type=entity_type,
                        operation=operation,
                    )
                )
        # USER entity type permissions (excluding CREATE)
        for operation in OperationType.owner_operations():
            if operation == OperationType.CREATE:
                continue
            await conn.execute(
                sa.insert(PermissionRow.__table__).values(
                    role_id=role_id,
                    scope_type=ScopeType.USER,
                    scope_id=str(user_uuid),
                    entity_type=EntityType.USER,
                    operation=operation,
                )
            )

    yield role_id

    async with db_engine.begin() as conn:
        await conn.execute(
            PermissionRow.__table__.delete().where(PermissionRow.__table__.c.role_id == role_id)
        )
        await conn.execute(
            AssociationScopesEntitiesRow.__table__.delete().where(
                (AssociationScopesEntitiesRow.__table__.c.entity_type == EntityType.ROLE)
                & (AssociationScopesEntitiesRow.__table__.c.entity_id == str(role_id))
            )
        )
        await conn.execute(
            UserRoleRow.__table__.delete().where(UserRoleRow.__table__.c.role_id == role_id)
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id == role_id))


# ---------------------------------------------------------------------------
# Session seeding with RBAC scope association
# ---------------------------------------------------------------------------


async def _seed_session(
    db_engine: SAEngine,
    *,
    domain_name: str,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
    access_key: str,
    scaling_group: str,
    status: SessionStatus = SessionStatus.RUNNING,
) -> SessionSeedData:
    """Insert a session + kernel row with RBAC scope association.

    Replicates what the scheduler does at session creation:
    SessionRow + kernel + AssociationScopesEntitiesRow (session → user scope, session → project scope).
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-session-{unique}"
    kernel_id = uuid.uuid4()
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        status.name: now.isoformat(),
    }

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_size=1,
                cluster_mode="single-node",
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                access_key=access_key,
                scaling_group_name=scaling_group,
                status=status,
                status_info="",
                status_history=status_history,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                created_at=now,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=kernel_id,
                session_id=session_id,
                session_creation_id=f"cid-{unique}",
                session_name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname="main0",
                cluster_mode="single-node",
                cluster_size=1,
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                access_key=access_key,
                scaling_group=scaling_group,
                status=KernelStatus.RUNNING,
                status_info="",
                occupied_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                created_at=now,
            )
        )
        # RBAC scope association: session → user scope (AUTO)
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__).values(
                scope_type=ScopeType.USER,
                scope_id=str(user_uuid),
                entity_type=EntityType.SESSION,
                entity_id=str(session_id),
                relation_type=RelationType.AUTO,
            )
        )
        # RBAC scope association: session → project scope (AUTO)
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__).values(
                scope_type=ScopeType.PROJECT,
                scope_id=str(group_id),
                entity_type=EntityType.SESSION,
                entity_id=str(session_id),
                relation_type=RelationType.AUTO,
            )
        )

    return SessionSeedData(
        session_id=session_id,
        session_name=session_name,
        kernel_id=kernel_id,
        access_key=access_key,
        domain_name=domain_name,
        user_uuid=user_uuid,
    )


async def _cleanup_session(db_engine: SAEngine, session_id: SessionId) -> None:
    """Remove session, kernel, and RBAC association rows."""
    async with db_engine.begin() as conn:
        await conn.execute(
            AssociationScopesEntitiesRow.__table__.delete().where(
                (AssociationScopesEntitiesRow.__table__.c.entity_type == EntityType.SESSION)
                & (AssociationScopesEntitiesRow.__table__.c.entity_id == str(session_id))
            )
        )
        await conn.execute(kernels.delete().where(kernels.c.session_id == session_id))
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )


@pytest.fixture()
async def admin_session_seed(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING session owned by the admin user."""
    seed = await _seed_session(
        db_engine,
        domain_name=domain_fixture.domain_name,
        group_id=group_fixture,
        user_uuid=admin_user_fixture.user_uuid,
        access_key=admin_user_fixture.keypair.access_key,
        scaling_group=scaling_group_fixture,
    )
    yield seed
    await _cleanup_session(db_engine, seed.session_id)


@pytest.fixture()
async def user_session_seed(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    group_fixture: uuid.UUID,
    regular_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
    user_system_role: uuid.UUID,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING session owned by the regular user.

    Depends on user_system_role to ensure the user has RBAC permissions.
    """
    seed = await _seed_session(
        db_engine,
        domain_name=domain_fixture.domain_name,
        group_id=group_fixture,
        user_uuid=regular_user_fixture.user_uuid,
        access_key=regular_user_fixture.keypair.access_key,
        scaling_group=scaling_group_fixture,
    )
    yield seed
    await _cleanup_session(db_engine, seed.session_id)
