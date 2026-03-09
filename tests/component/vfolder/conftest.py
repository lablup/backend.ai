from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.types import (
    HostPortPair,
    QuotaScopeID,
    QuotaScopeType,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderUsageMode,
)
from ai.backend.manager.actions.validators import ActionValidators

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api.rest.middleware import auth as _auth_api
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.vfolder.handler import VFolderHandler
from ai.backend.manager.api.rest.vfolder.registry import register_vfolder_routes
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.resource_policy import keypair_resource_policies
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    vfolder_invitations,
    vfolder_permissions,
    vfolders,
)
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.vfolder.processors.file import VFolderFileProcessors
from ai.backend.manager.services.vfolder.processors.invite import VFolderInviteProcessors
from ai.backend.manager.services.vfolder.processors.sharing import VFolderSharingProcessors
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors
from ai.backend.manager.services.vfolder.services.file import VFolderFileService
from ai.backend.manager.services.vfolder.services.invite import VFolderInviteService
from ai.backend.manager.services.vfolder.services.sharing import VFolderSharingService
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService

_VFOLDER_SERVER_SUBAPP_MODULES = (_auth_api,)

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


@pytest.fixture()
def async_etcd(
    bootstrap_config: Any,
) -> AsyncEtcd:
    etcd_config = bootstrap_config.etcd
    etcd_addr = etcd_config.addr
    if isinstance(etcd_addr, list):
        addrs: HostPortPair | list[HostPortPair] = [
            HostPortPair(host=a.host, port=a.port) for a in etcd_addr
        ]
    else:
        addrs = HostPortPair(host=etcd_addr.host, port=etcd_addr.port)
    return AsyncEtcd(
        addrs=addrs,
        namespace=etcd_config.namespace,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "global",
            ConfigScopes.SGROUP: "sgroup/default",
            ConfigScopes.NODE: "node/test",
        },
    )


@pytest.fixture()
def vfolder_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    async_etcd: AsyncEtcd,
    storage_manager: StorageSessionManager,
    background_task_manager: BackgroundTaskManager,
    valkey_clients: ValkeyClients,
) -> VFolderProcessors:
    vfolder_repository = VfolderRepository(database_engine)
    user_repository = UserRepository(database_engine)
    service = VFolderService(
        config_provider=config_provider,
        etcd=async_etcd,
        storage_manager=storage_manager,
        background_task_manager=background_task_manager,
        vfolder_repository=vfolder_repository,
        user_repository=user_repository,
        valkey_stat_client=valkey_clients.stat,
    )
    return VFolderProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def vfolder_file_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    storage_manager: StorageSessionManager,
) -> VFolderFileProcessors:
    vfolder_repository = VfolderRepository(database_engine)
    user_repository = UserRepository(database_engine)
    service = VFolderFileService(
        config_provider=config_provider,
        storage_manager=storage_manager,
        vfolder_repository=vfolder_repository,
        user_repository=user_repository,
    )
    return VFolderFileProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def vfolder_invite_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> VFolderInviteProcessors:
    vfolder_repository = VfolderRepository(database_engine)
    user_repository = UserRepository(database_engine)
    service = VFolderInviteService(
        config_provider=config_provider,
        vfolder_repository=vfolder_repository,
        user_repository=user_repository,
    )
    return VFolderInviteProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def vfolder_sharing_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> VFolderSharingProcessors:
    vfolder_repository = VfolderRepository(database_engine)
    user_repository = UserRepository(database_engine)
    service = VFolderSharingService(
        config_provider=config_provider,
        vfolder_repository=vfolder_repository,
        user_repository=user_repository,
    )
    return VFolderSharingProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    auth_processors: AuthProcessors,
    vfolder_processors: VFolderProcessors,
    vfolder_file_processors: VFolderFileProcessors,
    vfolder_invite_processors: VFolderInviteProcessors,
    vfolder_sharing_processors: VFolderSharingProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for vfolder-domain tests."""
    return [
        register_vfolder_routes(
            VFolderHandler(
                auth=auth_processors,
                vfolder=vfolder_processors,
                vfolder_file=vfolder_file_processors,
                vfolder_invite=vfolder_invite_processors,
                vfolder_sharing=vfolder_sharing_processors,
            ),
            route_deps,
            vfolder_processors=vfolder_processors,
        ),
    ]


@pytest.fixture()
async def vfolder_host_permission_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[None]:
    """Update allowed_vfolder_hosts on the test domain and keypair resource policy.

    Grants all VFolderHostPermission flags for the "local" host so that
    vfolder operations (create, rename, delete, invite, etc.) are permitted.
    """
    all_perms: set[VFolderHostPermission] = set(VFolderHostPermission)
    host_perms = VFolderHostPermissionMap({"local": all_perms})
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(domains)
            .where(domains.c.name == domain_fixture)
            .values(allowed_vfolder_hosts=host_perms)
        )
        await conn.execute(
            sa.update(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == resource_policy_fixture)
            .values(allowed_vfolder_hosts=host_perms)
        )
        # Also update the "default" keypair resource policy if it exists,
        # as new keypairs may reference it.
        await conn.execute(
            sa.update(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == "default")
            .values(allowed_vfolder_hosts=host_perms)
        )
    yield
    # Restore empty permissions on teardown
    empty_perms = VFolderHostPermissionMap()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(domains)
            .where(domains.c.name == domain_fixture)
            .values(allowed_vfolder_hosts=empty_perms)
        )
        await conn.execute(
            sa.update(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == resource_policy_fixture)
            .values(allowed_vfolder_hosts=empty_perms)
        )


@pytest.fixture()
async def vfolder_factory(
    db_engine: SAEngine,
    domain_fixture: str,
    admin_user_fixture: Any,
    vfolder_host_permission_fixture: None,
) -> AsyncIterator[VFolderFactory]:
    """Factory that inserts vfolder rows directly into DB (bypassing storage-proxy).

    This avoids the storage-proxy dependency for create operations.
    Yields a factory callable and cleans up all created vfolders on teardown.
    """
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
            "domain_name": domain_fixture,
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
            await conn.execute(sa.insert(vfolders).values(**defaults))
        created_ids.append(defaults["id"])
        return defaults

    yield _create

    # Cleanup: remove related rows first, then vfolders
    async with db_engine.begin() as conn:
        for vid in reversed(created_ids):
            await conn.execute(
                vfolder_invitations.delete().where(vfolder_invitations.c.vfolder == vid)
            )
            await conn.execute(
                vfolder_permissions.delete().where(vfolder_permissions.c.vfolder == vid)
            )
            await conn.execute(vfolders.delete().where(vfolders.c.id == vid))


@pytest.fixture()
async def target_vfolder(
    vfolder_factory: VFolderFactory,
) -> VFolderFixtureData:
    """Pre-created vfolder for tests that need an existing vfolder."""
    return await vfolder_factory()
