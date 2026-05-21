"""Component test fixtures for model card RBAC / project membership scenarios."""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.permission.types import EntityType, OperationType, ScopeType
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.bulk import BulkActionRBACValidator
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.model_card.handler import V2ModelCardHandler
from ai.backend.manager.api.rest.v2.model_card.registry import register_v2_model_card_routes
from ai.backend.manager.api.rest.v2.project.handler import V2ProjectHandler
from ai.backend.manager.api.rest.v2.project.registry import register_v2_project_routes
from ai.backend.manager.api.rest.v2.rbac.handler import V2RBACHandler
from ai.backend.manager.api.rest.v2.rbac.registry import register_v2_rbac_routes
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import vfolders
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.model_card.repository import ModelCardRepository
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.model_card.processors import ModelCardProcessors
from ai.backend.manager.services.model_card.service import ModelCardService
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.permission_contoller.service import PermissionControllerService
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData


def _build_validators(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> ActionValidators:
    permission_repo = PermissionControllerRepository(database_engine)
    return ActionValidators(
        rbac=RBACValidators(
            scope=ScopeActionRBACValidator(permission_repo, config_provider),
            single_entity=SingleEntityActionRBACValidator(permission_repo, config_provider),
            bulk=BulkActionRBACValidator(permission_repo, config_provider),
        ),
    )


@pytest.fixture()
def model_card_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: AsyncMock,
    config_provider: ManagerConfigProvider,
) -> ModelCardProcessors:
    """Real ModelCardProcessors with real RBAC enforcement."""
    repo = ModelCardRepository(database_engine)
    service = ModelCardService(repo, storage_manager)
    return ModelCardProcessors(
        service=service,
        action_monitors=[],
        validators=_build_validators(database_engine, config_provider),
    )


@pytest.fixture()
def group_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: AsyncMock,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
) -> GroupProcessors:
    """Real GroupProcessors with real RBAC enforcement."""
    repo = GroupRepository(
        database_engine,
        config_provider,
        valkey_clients.stat,
        storage_manager,
    )
    repositories = GroupRepositories(repository=repo)
    service = GroupService(
        storage_manager=storage_manager,
        config_provider=config_provider,
        valkey_stat_client=valkey_clients.stat,
        group_repositories=repositories,
    )
    return GroupProcessors(
        group_service=service,
        action_monitors=[],
        validators=_build_validators(database_engine, config_provider),
    )


@pytest.fixture()
def permission_controller_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: AsyncMock,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
) -> PermissionControllerProcessors:
    """Real PermissionControllerProcessors for role assign/revoke SDK calls."""
    perm_repo = PermissionControllerRepository(database_engine)
    group_repo = GroupRepository(
        database_engine, config_provider, valkey_clients.stat, storage_manager
    )
    service = PermissionControllerService(
        perm_repo, group_repository=group_repo, rbac_action_registry=[]
    )
    return PermissionControllerProcessors(
        service=service,
        action_monitors=[],
        validators=_build_validators(database_engine, config_provider),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    model_card_processors: ModelCardProcessors,
    group_processors: GroupProcessors,
    permission_controller_processors: PermissionControllerProcessors,
) -> list[RouteRegistry]:
    """Register v2 model-card, project, and RBAC routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.model_card = model_card_processors
    processors.group = group_processors
    processors.permission_controller = permission_controller_processors

    mc_handler = V2ModelCardHandler(adapter=ModelCardAdapter(processors))
    proj_handler = V2ProjectHandler(adapter=ProjectAdapter(processors))
    rbac_handler = V2RBACHandler(adapter=RBACAdapter(processors))

    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_model_card_routes(mc_handler, route_deps))
    v2_reg.add_subregistry(register_v2_project_routes(proj_handler, route_deps))
    v2_reg.add_subregistry(register_v2_rbac_routes(rbac_handler, route_deps))
    return [v2_reg]


# ---------------------------------------------------------------------------
# DB-seeded fixtures (entities not exposed via SDK or requiring storage proxy)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def model_store_project_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Insert a MODEL_STORE type project and yield its UUID."""
    project_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=project_id,
                name=f"model-store-{secrets.token_hex(6)}",
                description="Test MODEL_STORE project",
                is_active=True,
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
                type=ProjectType.MODEL_STORE,
            )
        )
    yield project_id
    async with db_engine.begin() as conn:
        await conn.execute(
            ModelCardRow.__table__.delete().where(ModelCardRow.__table__.c.project == project_id)
        )
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == project_id))


@pytest.fixture()
async def second_project_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Insert a second MODEL_STORE project for cross-project isolation tests."""
    project_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=project_id,
                name=f"model-store-b-{secrets.token_hex(6)}",
                description="Second MODEL_STORE project",
                is_active=True,
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
                type=ProjectType.MODEL_STORE,
            )
        )
    yield project_id
    async with db_engine.begin() as conn:
        await conn.execute(
            ModelCardRow.__table__.delete().where(ModelCardRow.__table__.c.project == project_id)
        )
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == project_id))


@pytest.fixture()
async def vfolder_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    admin_user_fixture: Any,
) -> AsyncIterator[VFolderUUID]:
    """Insert a MODEL-usage vfolder (storage proxy is mocked)."""
    vfolder_id = VFolderUUID(uuid.uuid4())
    user_uuid = admin_user_fixture.user_uuid
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(vfolders).values(
                id=vfolder_id,
                name=f"test-model-vfolder-{secrets.token_hex(4)}",
                host="local",
                domain_name=domain_fixture,
                quota_scope_id=str(QuotaScopeID(QuotaScopeType.USER, user_uuid)),
                usage_mode=VFolderUsageMode.MODEL,
                user=str(user_uuid),
            )
        )
    yield vfolder_id
    async with db_engine.begin() as conn:
        await conn.execute(
            ModelCardRow.__table__.delete().where(ModelCardRow.__table__.c.vfolder == vfolder_id)
        )
        await conn.execute(vfolders.delete().where(vfolders.c.id == vfolder_id))


@pytest.fixture()
async def role_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Insert a project member role for assign_users SDK calls."""
    role_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name=f"test-member-{secrets.token_hex(4)}",
                status=RoleStatus.ACTIVE,
            )
        )
    yield role_id
    async with db_engine.begin() as conn:
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id == role_id))


@pytest.fixture(autouse=True)
async def _register_role_in_project(
    db_engine: SAEngine,
    role_fixture: uuid.UUID,
    model_store_project_fixture: uuid.UUID,
) -> AsyncIterator[None]:
    """Register the test role in the primary project scope via ASE.

    This ensures revoke_role() can detect the role as project-scoped
    and properly calls unbind_user_from_project() to clean up agus entries.
    """
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__).values(
                scope_type=ScopeType.PROJECT,
                scope_id=str(model_store_project_fixture),
                entity_type=EntityType.ROLE,
                entity_id=str(role_fixture),
            )
        )
    yield
    async with db_engine.begin() as conn:
        await conn.execute(
            AssociationScopesEntitiesRow.__table__.delete().where(
                sa.and_(
                    AssociationScopesEntitiesRow.__table__.c.entity_type == EntityType.ROLE,
                    AssociationScopesEntitiesRow.__table__.c.entity_id == str(role_fixture),
                )
            )
        )


@pytest.fixture(autouse=True)
async def _grant_model_card_read_permission(
    db_engine: SAEngine,
    role_fixture: uuid.UUID,
    model_store_project_fixture: uuid.UUID,
) -> AsyncIterator[None]:
    """Grant model_card:read permission to the test role at the project scope.

    Required for the regular user to pass RBAC enforcement on
    search_in_project (ScopeActionRBACValidator checks this permission).
    """
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(PermissionRow.__table__).values(
                role_id=role_fixture,
                scope_type=ScopeType.PROJECT,
                scope_id=str(model_store_project_fixture),
                entity_type=EntityType.MODEL_CARD,
                operation=OperationType.READ,
            )
        )
    yield
    async with db_engine.begin() as conn:
        await conn.execute(
            PermissionRow.__table__.delete().where(
                PermissionRow.__table__.c.role_id == role_fixture
            )
        )


# ---------------------------------------------------------------------------
# V2 SDK client registries
# ---------------------------------------------------------------------------


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """V2ClientRegistry authenticated as superadmin."""
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
    """V2ClientRegistry authenticated as regular user."""
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
