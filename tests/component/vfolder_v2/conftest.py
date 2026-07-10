"""Component test fixtures for v2 VFolder GET endpoint with RBAC validation."""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderUsageMode,
)
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.vfolder.handler import V2VFolderHandler
from ai.backend.manager.api.rest.v2.vfolder.registry import register_v2_vfolder_routes
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.resource_policy import keypair_resource_policies
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import vfolders
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
    from tests.component.conftest import ServerInfo, UserFixtureData


@dataclass(frozen=True)
class VFolderFixtureData:
    id: uuid.UUID
    name: str
    host: str
    domain_name: str
    quota_scope_id: str
    usage_mode: VFolderUsageMode
    permission: VFolderMountPermission
    ownership_type: VFolderOwnershipType
    user: str
    creator: str
    status: VFolderOperationStatus
    cloneable: bool


VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


@pytest.fixture()
def rbac_permission_repo(
    database_engine: ExtendedAsyncSAEngine,
) -> PermissionControllerRepository:
    """Real permission controller repository backed by real DB."""
    return PermissionControllerRepository(database_engine)


@pytest.fixture()
def vfolder_processors(
    database_engine: ExtendedAsyncSAEngine,
    rbac_permission_repo: PermissionControllerRepository,
) -> VFolderProcessors:
    """VFolderProcessors with real SingleEntityActionRBACValidator.

    RBAC checks use check_permission_with_scope_chain() against the real DB.
    Without explicit RBAC permission grants, all access is denied (403).
    """
    vfolder_repository = VfolderRepository(database_engine)
    user_repository = UserRepository(database_engine)
    service = VFolderService(
        config_provider=MagicMock(),
        etcd=MagicMock(),
        storage_manager=MagicMock(),
        background_task_manager=MagicMock(),
        vfolder_repository=vfolder_repository,
        user_repository=user_repository,
        valkey_stat_client=MagicMock(),
    )
    real_single_entity_validator = SingleEntityActionRBACValidator(
        rbac_permission_repo, MagicMock()
    )
    return VFolderProcessors(
        service=service,
        action_monitors=[],
        validators=ActionValidators(
            rbac=RBACValidators(
                scope=AsyncMock(),
                single_entity=real_single_entity_validator,
                bulk=AsyncMock(),
            )
        ),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    vfolder_processors: VFolderProcessors,
) -> list[RouteRegistry]:
    """Register v2 vfolder routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.vfolder = vfolder_processors
    adapter = VFolderAdapter(processors)
    handler = V2VFolderHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_vfolder_routes(handler, route_deps))
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
async def vfolder_host_permission_fixture(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
) -> AsyncIterator[None]:
    """Grant all VFolderHostPermission flags for the 'local' host."""
    all_perms: set[VFolderHostPermission] = set(VFolderHostPermission)
    host_perms = VFolderHostPermissionMap({"local": all_perms})
    async with db_engine.begin() as conn:
        await conn.execute(
            domains.update()
            .where(domains.c.name == domain_fixture.domain_name)
            .values(allowed_vfolder_hosts=host_perms)
        )
        await conn.execute(
            keypair_resource_policies.update()
            .where(keypair_resource_policies.c.name == resource_policy_fixture)
            .values(allowed_vfolder_hosts=host_perms)
        )
        await conn.execute(
            keypair_resource_policies.update()
            .where(keypair_resource_policies.c.name == "default")
            .values(allowed_vfolder_hosts=host_perms)
        )
    yield
    empty_perms = VFolderHostPermissionMap()
    async with db_engine.begin() as conn:
        await conn.execute(
            domains.update()
            .where(domains.c.name == domain_fixture.domain_name)
            .values(allowed_vfolder_hosts=empty_perms)
        )
        await conn.execute(
            keypair_resource_policies.update()
            .where(keypair_resource_policies.c.name == resource_policy_fixture)
            .values(allowed_vfolder_hosts=empty_perms)
        )


@pytest.fixture()
async def vfolder_factory(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    admin_user_fixture: UserFixtureData,
    vfolder_host_permission_fixture: None,
) -> AsyncIterator[VFolderFactory]:
    """Factory that inserts vfolder rows directly into DB (bypassing storage-proxy)."""
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> VFolderFixtureData:
        unique = secrets.token_hex(4)
        vfolder_id = uuid.uuid4()
        user_uuid = admin_user_fixture.user_uuid
        quota_scope_id = QuotaScopeID(
            scope_type=QuotaScopeType.USER,
            scope_id=user_uuid,
        )
        defaults: dict[str, Any] = {
            "id": vfolder_id,
            "name": f"test-vfolder-{unique}",
            "host": "local",
            "domain_name": domain_fixture.domain_name,
            "quota_scope_id": str(quota_scope_id),
            "usage_mode": VFolderUsageMode.GENERAL,
            "permission": VFolderMountPermission.READ_WRITE,
            "ownership_type": VFolderOwnershipType.USER,
            "user": str(user_uuid),
            "creator": "admin-test@test.local",
            "status": VFolderOperationStatus.READY,
            "cloneable": False,
        }
        defaults.update(overrides)
        async with db_engine.begin() as conn:
            await conn.execute(vfolders.insert().values(**defaults))
        created_ids.append(defaults["id"])
        return VFolderFixtureData(**defaults)

    yield _create

    async with db_engine.begin() as conn:
        for vid in reversed(created_ids):
            await conn.execute(vfolders.delete().where(vfolders.c.id == vid))


@pytest.fixture()
async def vfolder_owned_by_admin(
    vfolder_factory: VFolderFactory,
) -> VFolderFixtureData:
    """Pre-created vfolder owned by the admin user."""
    return await vfolder_factory()


@pytest.fixture()
async def vfolder_owned_by_regular_user(
    vfolder_factory: VFolderFactory,
    regular_user_fixture: UserFixtureData,
) -> VFolderFixtureData:
    """Pre-created vfolder owned by the regular (non-admin) user."""
    user_uuid = regular_user_fixture.user_uuid
    return await vfolder_factory(
        user=str(user_uuid),
        creator="user-test@test.local",
        quota_scope_id=str(QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=user_uuid)),
    )
