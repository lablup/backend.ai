from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any, Protocol
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.dotfile import DotfileFieldType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.config import (
    CreateDomainDotfileRequest,
    CreateDotfileResponse,
    CreateGroupDotfileRequest,
    CreateUserDotfileRequest,
    DeleteDomainDotfileRequest,
    DeleteGroupDotfileRequest,
    DeleteUserDotfileRequest,
)
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.validators.build import build_action_validators
from ai.backend.manager.api.adapters.user.config import UserConfigAdapter
from ai.backend.manager.api.rest.domainconfig.handler import DomainConfigHandler
from ai.backend.manager.api.rest.domainconfig.registry import register_domainconfig_routes
from ai.backend.manager.api.rest.groupconfig.handler import GroupConfigHandler
from ai.backend.manager.api.rest.groupconfig.registry import register_groupconfig_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.userconfig.handler import UserConfigHandler
from ai.backend.manager.api.rest.userconfig.registry import register_userconfig_routes
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.bootstrap_script.row import (
    BootstrapScriptRow,
    UserDefaultBootstrapScriptRow,
)
from ai.backend.manager.models.bootstrap_script_revision.row import BootstrapScriptRevisionRow
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.domain.provider import DomainOpsProvider
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.dotfile.actions.lookup_owner import (
    LookupBulkDotfileOwnerAction,
    LookupDotfileOwnerAction,
)
from ai.backend.manager.services.dotfile.processors import DotfileProcessors
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.project.service import ProjectService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.testutils.fixtures import DomainFixtureData
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


class UserFixture(Protocol):
    user_uuid: UserID


UserDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]
GroupDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]
DomainDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]


@pytest.fixture(autouse=True)
async def user_permission_scope(
    database_engine: ExtendedAsyncSAEngine,
    regular_user_fixture: UserFixture,
) -> None:
    async with database_engine.begin_session() as session:
        await VirtualEntitySeeder().provision(
            session, UserEntityType(), regular_user_fixture.user_uuid
        )
        role = RoleRow(
            name=f"user-self-{regular_user_fixture.user_uuid}",
            status=RoleStatus.ACTIVE,
            scope_type=UserEntityType(),
            scope_id=regular_user_fixture.user_uuid,
        )
        session.add(role)
        await session.flush()
        session.add_all([
            PermissionRow(
                role_id=role.id,
                entity_type=UserEntityType(),
                permission=permission,
            )
            for permission in (Permission.READ, Permission.UPDATE)
        ])
        session.add(UserRoleRow(user_id=regular_user_fixture.user_uuid, role_id=role.id))


@pytest.fixture()
def config_registry(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> ProcessorRegistry[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=build_action_validators(
                RbacPermissionCheckRepository(
                    PermissionOpsProvider(database_engine), config_provider
                ),
                config_provider,
            ),
            repository=OpsRepository(V2DBOpsProvider(database_engine)),
        )
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    database_engine: ExtendedAsyncSAEngine,
    config_registry: ProcessorRegistry[Any],
    auth_processors: AuthProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for config-domain tests."""
    v2_ops = V2DBOpsProvider(database_engine)
    domain = DomainProcessors(
        config_registry.group(GroupMeta(DomainEntityType())),
        DomainService(DomainRepository(database_engine, DomainOpsProvider(database_engine))),
    )
    project = ProjectProcessors(
        config_registry.group(GroupMeta(ProjectEntityType())),
        ProjectService(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(
                repository=ProjectRepository(
                    database_engine,
                    v2_ops,
                    ResourcePolicyOpsProvider(database_engine),
                    MagicMock(),
                    MagicMock(),
                    MagicMock(),
                )
            ),
        ),
    )
    user = UserProcessors(
        config_registry.group(GroupMeta(UserEntityType())),
        UserService(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            UserRepository(
                database_engine,
                v2_ops,
                ShareOpsProvider(database_engine),
                ResourcePolicyOpsProvider(database_engine),
                KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
            ),
            MagicMock(),
        ),
    )
    return [
        register_groupconfig_routes(GroupConfigHandler(project=project), route_deps),
        register_userconfig_routes(
            UserConfigHandler(
                auth=auth_processors,
                user=user,
                user_config=UserConfigAdapter(
                    user,
                    DotfileProcessors(
                        config_registry.dangling_lookup_field_group(
                            FieldGroupMeta(DotfileFieldType()),
                            DotfileData,
                            LookupDotfileOwnerAction,
                            LookupBulkDotfileOwnerAction,
                        )
                    ),
                ),
            ),
            route_deps,
        ),
        register_domainconfig_routes(DomainConfigHandler(domain=domain), route_deps),
    ]


@pytest.fixture()
async def user_dotfile_factory(
    admin_registry: BackendAIClientRegistry,
    database_engine: ExtendedAsyncSAEngine,
    admin_user_fixture: UserFixture,
) -> AsyncIterator[UserDotfileFactory]:
    """Create through HTTP, seed the default flag, and delete on teardown."""
    created_paths: list[str] = []

    async def _create(**overrides: Any) -> CreateDotfileResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "path": f".test-dotfile-{unique}",
            "data": f"# test content {unique}",
            "permission": "644",
        }
        params.update(overrides)
        result = await admin_registry.config.create_user_dotfile(CreateUserDotfileRequest(**params))
        async with database_engine.begin_session() as session:
            dotfile_id = await session.scalar(
                sa.select(DotfileRow.id).where(
                    DotfileRow.entity_type == UserEntityType(),
                    DotfileRow.entity_id == admin_user_fixture.user_uuid,
                    DotfileRow.path == params["path"],
                )
            )
        assert dotfile_id is not None
        async with database_engine.begin() as conn:
            await conn.execute(
                sa.update(DotfileRow).where(DotfileRow.id == dotfile_id).values(is_default=True)
            )
        created_paths.append(params["path"])
        return result

    yield _create

    for path in reversed(created_paths):
        try:
            await admin_registry.config.delete_user_dotfile(DeleteUserDotfileRequest(path=path))
        except Exception:
            pass


@pytest.fixture()
async def group_dotfile_factory(
    admin_registry: BackendAIClientRegistry,
    group_fixture: uuid.UUID,
) -> AsyncIterator[GroupDotfileFactory]:
    """Factory fixture that creates group dotfiles via SDK and deletes on teardown."""
    created_paths: list[str] = []

    async def _create(**overrides: Any) -> CreateDotfileResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "group": str(group_fixture),
            "path": f".test-group-dotfile-{unique}",
            "data": f"# group test content {unique}",
            "permission": "644",
        }
        params.update(overrides)
        result = await admin_registry.config.create_group_dotfile(
            CreateGroupDotfileRequest(**params)
        )
        created_paths.append(params["path"])
        return result

    yield _create

    for path in reversed(created_paths):
        try:
            await admin_registry.config.delete_group_dotfile(
                DeleteGroupDotfileRequest(group=str(group_fixture), path=path)
            )
        except Exception:
            pass


@pytest.fixture()
async def domain_dotfile_factory(
    admin_registry: BackendAIClientRegistry,
    domain_fixture: DomainFixtureData,
) -> AsyncIterator[DomainDotfileFactory]:
    """Factory fixture that creates domain dotfiles via SDK and deletes on teardown."""
    created_paths: list[str] = []

    async def _create(**overrides: Any) -> CreateDotfileResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "domain": domain_fixture.domain_name,
            "path": f".test-domain-dotfile-{unique}",
            "data": f"# domain test content {unique}",
            "permission": "644",
        }
        params.update(overrides)
        result = await admin_registry.config.create_domain_dotfile(
            CreateDomainDotfileRequest(**params)
        )
        created_paths.append(params["path"])
        return result

    yield _create

    for path in reversed(created_paths):
        try:
            await admin_registry.config.delete_domain_dotfile(
                DeleteDomainDotfileRequest(domain=domain_fixture.domain_name, path=path)
            )
        except Exception:
            pass


@pytest.fixture()
async def default_bootstrap_scripts(
    db_engine: SAEngine,
    admin_registry: BackendAIClientRegistry,
    user_registry: BackendAIClientRegistry,
) -> AsyncIterator[None]:
    """Give every user an empty default bootstrap script."""
    async with db_engine.begin() as conn:
        scripts = (
            await conn.execute(
                sa.insert(BootstrapScriptRow)
                .from_select(
                    ["entity_type", "entity_id"],
                    sa.select(sa.literal(UserEntityType()), UserRow.uuid),
                )
                .returning(BootstrapScriptRow.id, BootstrapScriptRow.entity_id)
            )
        ).all()
        if scripts:
            await conn.execute(
                sa.insert(BootstrapScriptRevisionRow),
                [{"script_id": sid, "revision_number": 1, "script": ""} for sid, _ in scripts],
            )
            await conn.execute(
                sa.insert(UserDefaultBootstrapScriptRow),
                [{"user_id": uid, "script_id": sid} for sid, uid in scripts],
            )
    try:
        yield
    finally:
        async with db_engine.begin() as conn:
            await conn.execute(sa.delete(BootstrapScriptRow))


@pytest.fixture()
async def no_default_bootstrap_scripts(db_engine: SAEngine) -> AsyncIterator[None]:
    """Leave every user without a bootstrap script, and remove what the test wrote."""
    try:
        yield
    finally:
        async with db_engine.begin() as conn:
            await conn.execute(sa.delete(BootstrapScriptRow))


@pytest.fixture
async def non_default_user_access_key(
    db_engine: SAEngine,
    regular_user_fixture: UserFixture,
    resource_policy_fixture: str,
) -> AsyncIterator[str]:
    access_key = f"AKTEST{secrets.token_hex(7).upper()}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(KeyPairRow).values(
                access_key=access_key,
                secret_key=SecretValue(secrets.token_hex(20)),
                user=regular_user_fixture.user_uuid,
                is_active=True,
                is_admin=False,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
            )
        )
        await conn.execute(
            sa.insert(DotfileRow).values(
                entity_type=UserEntityType(),
                entity_id=regular_user_fixture.user_uuid,
                path=".shared-user",
                perm="600",
                data="user",
                is_default=True,
            )
        )
    yield access_key
    async with db_engine.begin() as conn:
        await conn.execute(sa.delete(KeyPairRow).where(KeyPairRow.access_key == access_key))


@pytest.fixture
async def regular_user_reads_admin(
    database_engine: ExtendedAsyncSAEngine,
    regular_user_fixture: UserFixture,
    admin_user_fixture: UserFixture,
) -> None:
    async with database_engine.begin_session() as session:
        await VirtualEntitySeeder().provision(
            session, UserEntityType(), admin_user_fixture.user_uuid
        )
        role = RoleRow(
            name=f"read-admin-{regular_user_fixture.user_uuid}",
            status=RoleStatus.ACTIVE,
            scope_type=UserEntityType(),
            scope_id=admin_user_fixture.user_uuid,
        )
        session.add(role)
        await session.flush()
        session.add(
            PermissionRow(role_id=role.id, entity_type=UserEntityType(), permission=Permission.READ)
        )
        session.add(UserRoleRow(user_id=regular_user_fixture.user_uuid, role_id=role.id))


@pytest.fixture
async def admin_access_key(
    db_engine: SAEngine,
    admin_user_fixture: UserFixture,
) -> str:
    async with db_engine.begin() as conn:
        key = await conn.scalar(
            sa.select(KeyPairRow.access_key).where(
                KeyPairRow.user == admin_user_fixture.user_uuid, KeyPairRow.is_default
            )
        )
    assert key is not None
    return key
