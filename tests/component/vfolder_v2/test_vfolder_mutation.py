"""Component tests for v2 VFolder RBAC-enforced delete, restore, and purge mutations via SDK.

Exercises delete, restore, and purge mutations through the real HTTP server +
V2ClientRegistry SDK.
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.field import VFolderPermissionField
from ai.backend.common.dto.manager.v2.vfolder.request import CreateVFolderInScopeInput
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
from ai.backend.manager.api.adapters.vfolder import VFolderAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.vfolder.handler import V2VFolderHandler
from ai.backend.manager.api.rest.v2.vfolder.registry import register_v2_vfolder_routes
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
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

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
    from tests.component.conftest import ServerInfo, UserFixtureData


@dataclass(frozen=True)
class ProjectVFolderFixtureData:
    id: uuid.UUID
    project_id: uuid.UUID


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture()
def rbac_permission_repo(
    database_engine: ExtendedAsyncSAEngine,
) -> PermissionControllerRepository:
    return PermissionControllerRepository(database_engine)


@pytest.fixture()
def vfolder_processors(
    database_engine: ExtendedAsyncSAEngine,
    rbac_permission_repo: PermissionControllerRepository,
) -> VFolderProcessors:
    """Override: real scope + single-entity RBAC validators."""
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
    return VFolderProcessors(
        service=service,
        action_monitors=[],
        validators=ActionValidators(
            rbac=RBACValidators(
                scope=ScopeActionRBACValidator(rbac_permission_repo),
                single_entity=SingleEntityActionRBACValidator(rbac_permission_repo),
            )
        ),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    vfolder_processors: VFolderProcessors,
) -> list[RouteRegistry]:
    """Register v2 vfolder REST routes with real RBAC."""
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
async def project_vfolder(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    vfolder_host_permission_fixture: None,
) -> AsyncIterator[ProjectVFolderFixtureData]:
    """Seed a project-owned vfolder row directly in the DB."""
    unique = secrets.token_hex(4)
    vfolder_id = uuid.uuid4()
    quota_scope_id = QuotaScopeID(scope_type=QuotaScopeType.PROJECT, scope_id=group_fixture)
    async with db_engine.begin() as conn:
        await conn.execute(
            vfolders.insert().values(
                id=vfolder_id,
                name=f"test-proj-vfolder-{unique}",
                host="local",
                domain_name=domain_fixture,
                quota_scope_id=str(quota_scope_id),
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderMountPermission.READ_WRITE,
                ownership_type=VFolderOwnershipType.GROUP,
                user=None,
                group=group_fixture,
                creator="admin-test@test.local",
                status=VFolderOperationStatus.READY,
                cloneable=False,
            )
        )
    yield ProjectVFolderFixtureData(id=vfolder_id, project_id=group_fixture)
    async with db_engine.begin() as conn:
        await conn.execute(vfolders.delete().where(vfolders.c.id == vfolder_id))


# -- Tests -------------------------------------------------------------------


class TestDeleteVFolderRBAC:
    """DELETE /v2/vfolders/{id} -- SingleEntityActionProcessor RBAC."""

    async def test_regular_user_denied(
        self,
        user_v2_registry: V2ClientRegistry,
        project_vfolder: ProjectVFolderFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.vfolder.delete(project_vfolder.id)

    async def test_superadmin_succeeds(
        self,
        admin_v2_registry: V2ClientRegistry,
        project_vfolder: ProjectVFolderFixtureData,
    ) -> None:
        payload = await admin_v2_registry.vfolder.delete(project_vfolder.id)
        assert payload.id == project_vfolder.id


class TestRestoreVFolderRBAC:
    """POST /v2/vfolders/{id}/restore -- SingleEntityActionProcessor RBAC."""

    async def test_regular_user_denied(
        self,
        user_v2_registry: V2ClientRegistry,
        project_vfolder: ProjectVFolderFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.vfolder.restore(project_vfolder.id)

    async def test_superadmin_trash_then_restore(
        self,
        admin_v2_registry: V2ClientRegistry,
        project_vfolder: ProjectVFolderFixtureData,
    ) -> None:
        await admin_v2_registry.vfolder.delete(project_vfolder.id)
        payload = await admin_v2_registry.vfolder.restore(project_vfolder.id)
        assert payload.id == project_vfolder.id


class TestPurgeVFolderRBAC:
    """POST /v2/vfolders/{id}/purge -- SingleEntityActionProcessor RBAC."""

    async def test_regular_user_denied(
        self,
        user_v2_registry: V2ClientRegistry,
        project_vfolder: ProjectVFolderFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.vfolder.purge(project_vfolder.id)


class TestCreateVFolderInProjectRBAC:
    """POST /v2/vfolders/projects/{project_id} -- ScopeActionProcessor RBAC."""

    async def test_regular_user_denied(
        self,
        user_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """Regular user without project CREATE permission is denied before service runs."""
        request = CreateVFolderInScopeInput(
            name=f"rbac-denied-{secrets.token_hex(4)}",
            host="local",
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderPermissionField.READ_WRITE,
            cloneable=False,
        )
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.vfolder.create_in_project(group_fixture, request)
