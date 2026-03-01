from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderUsageMode,
)

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import vfolder as _vfolder_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.rest.auth.registry import register_auth_module
from ai.backend.manager.api.rest.types import ModuleRegistrar
from ai.backend.manager.api.rest.vfolder.registry import register_vfolder_module
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.resource_policy import keypair_resource_policies
from ai.backend.manager.models.vfolder import (
    vfolder_invitations,
    vfolder_permissions,
    vfolders,
)
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.server import (
    background_task_ctx,
    database_ctx,
    event_hub_ctx,
    event_producer_ctx,
    message_queue_ctx,
    monitoring_ctx,
    redis_ctx,
    storage_manager_ctx,
)
from ai.backend.manager.services.processors import ProcessorArgs, Processors, ServiceArgs

_VFOLDER_SERVER_SUBAPP_MODULES = (_auth_api, _vfolder_api)

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


@asynccontextmanager
async def _vfolder_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for vfolder-domain component tests.

    Relies on the preceding cleanup contexts having already initialized:
    - redis_ctx      → root_ctx.valkey_* (all 8 clients)
    - database_ctx   → root_ctx.db
    - monitoring_ctx → root_ctx.error_monitor / stats_monitor
    - storage_manager_ctx  → root_ctx.storage_manager
    - message_queue_ctx    → root_ctx.message_queue
    - event_producer_ctx   → root_ctx.event_producer / event_fetcher
    - event_hub_ctx        → root_ctx.event_hub
    - background_task_ctx  → root_ctx.background_task_manager

    Only agent_registry is left as MagicMock because it requires live gRPC
    connections to real agents, which are not available in component tests.
    """
    # _TestConfigProvider skips super().__init__() so _legacy_etcd_config_loader
    # is never set.  The @server_status_required decorator (used by all vfolder
    # handlers) calls config_provider.legacy_etcd_config_loader.get_manager_status()
    # which is async.  Inject a MagicMock with AsyncMock methods so the checks pass.
    mock_legacy_loader = MagicMock()
    mock_legacy_loader.get_manager_status = AsyncMock(return_value=ManagerStatus.RUNNING)
    mock_legacy_loader.get_vfolder_types = AsyncMock(return_value=["user", "group"])
    root_ctx.config_provider._legacy_etcd_config_loader = mock_legacy_loader

    root_ctx.repositories = Repositories.create(
        RepositoryArgs(
            db=root_ctx.db,
            storage_manager=root_ctx.storage_manager,
            config_provider=root_ctx.config_provider,
            valkey_stat_client=root_ctx.valkey_stat,
            valkey_schedule_client=root_ctx.valkey_schedule,
            valkey_image_client=root_ctx.valkey_image,
            valkey_live_client=root_ctx.valkey_live,
        )
    )
    root_ctx.processors = Processors.create(
        ProcessorArgs(
            service_args=ServiceArgs(
                db=root_ctx.db,
                repositories=root_ctx.repositories,
                etcd=root_ctx.etcd,
                config_provider=root_ctx.config_provider,
                storage_manager=root_ctx.storage_manager,
                valkey_stat_client=root_ctx.valkey_stat,
                valkey_live=root_ctx.valkey_live,
                valkey_artifact_client=root_ctx.valkey_artifact,
                error_monitor=root_ctx.error_monitor,
                event_fetcher=root_ctx.event_fetcher,
                background_task_manager=root_ctx.background_task_manager,
                event_hub=root_ctx.event_hub,
                event_producer=root_ctx.event_producer,
                # agent_registry requires gRPC connections to real agents — not feasible
                # in the component test environment; kept as MagicMock.
                agent_registry=MagicMock(),
                idle_checker_host=MagicMock(),
                event_dispatcher=MagicMock(),
                hook_plugin_ctx=MagicMock(),
                scheduling_controller=MagicMock(),
                deployment_controller=MagicMock(),
                revision_generator_registry=MagicMock(),
                agent_cache=MagicMock(),
                notification_center=MagicMock(),
                appproxy_client_pool=MagicMock(),
                prometheus_client=MagicMock(),
            ),
        ),
        [],
    )
    yield


@pytest.fixture()
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for vfolder-domain tests."""
    return [register_auth_module, register_vfolder_module]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for vfolder-domain component tests.

    Uses production contexts from server.py for real infrastructure:
    - redis_ctx: all 8 Valkey clients
    - database_ctx: real database connection
    - monitoring_ctx: real (empty-plugin) error and stats monitors
    - storage_manager_ctx: real StorageSessionManager (empty proxy config)
    - message_queue_ctx: real Redis-backed message queue
    - event_producer_ctx: real EventProducer + EventFetcher
    - event_hub_ctx: real EventHub
    - background_task_ctx: real BackgroundTaskManager
    - _vfolder_domain_ctx: repositories and processors wired with real clients
    """
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _vfolder_domain_ctx,
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
