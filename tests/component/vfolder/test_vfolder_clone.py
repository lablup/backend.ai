"""Component tests for VFolder clone policy enforcement.

Verifies that clone operations check the *user's* resource policy for
max_vfolder_count, not the source project's resource policy (BA-5520).

Storage proxy is mocked; the database is real.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.bgtask.types import TaskID
from ai.backend.common.dto.manager.v2.vfolder.request import CloneVFolderInput
from ai.backend.common.dto.manager.vfolder import CloneVFolderReq
from ai.backend.common.types import QuotaScopeID, QuotaScopeType
from ai.backend.manager.api.adapters.vfolder import VFolderAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.vfolder.handler import V2VFolderHandler
from ai.backend.manager.api.rest.v2.vfolder.registry import register_v2_vfolder_routes
from ai.backend.manager.api.rest.vfolder.handler import VFolderHandler
from ai.backend.manager.api.rest.vfolder.registry import register_vfolder_routes
from ai.backend.manager.data.vfolder.types import VFolderOwnershipType
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.vfolder.admin_repository import VFolderAdminRepository
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.vfolder.processors.file import VFolderFileProcessors
from ai.backend.manager.services.vfolder.processors.invite import VFolderInviteProcessors
from ai.backend.manager.services.vfolder.processors.sharing import VFolderSharingProcessors
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors
from ai.backend.manager.services.vfolder.processors.vfolder_admin import VFolderAdminProcessors
from ai.backend.manager.services.vfolder.services.vfolder_admin import VFolderAdminService

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


# ---------------------------------------------------------------------------
# Override server_module_registries to include both v1 and v2 routes
# ---------------------------------------------------------------------------


@pytest.fixture()
def vfolder_admin_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> VFolderAdminProcessors:
    repo = VFolderAdminRepository(database_engine)
    service = VFolderAdminService(vfolder_admin_repository=repo)
    return VFolderAdminProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    auth_processors: AuthProcessors,
    vfolder_processors: VFolderProcessors,
    vfolder_admin_processors: VFolderAdminProcessors,
    vfolder_file_processors: VFolderFileProcessors,
    vfolder_invite_processors: VFolderInviteProcessors,
    vfolder_sharing_processors: VFolderSharingProcessors,
) -> list[RouteRegistry]:
    """Register both v1 and v2 vfolder REST routes."""
    # v1
    v1_reg = register_vfolder_routes(
        VFolderHandler(
            auth=auth_processors,
            vfolder=vfolder_processors,
            vfolder_file=vfolder_file_processors,
            vfolder_invite=vfolder_invite_processors,
            vfolder_sharing=vfolder_sharing_processors,
        ),
        route_deps,
        vfolder_processors=vfolder_processors,
    )
    # v2
    processors = MagicMock(spec=Processors)
    processors.vfolder = vfolder_processors
    processors.vfolder_admin = vfolder_admin_processors
    adapter = VFolderAdapter(processors)
    handler = V2VFolderHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_vfolder_routes(handler, route_deps))
    return [v1_reg, v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with superadmin keypair."""
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


# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------


def _configure_clone_storage_mock(storage_manager: StorageSessionManager) -> AsyncMock:
    """Configure the storage mock for clone operations.

    Returns the mock client for further configuration if needed.
    """
    mock_client = AsyncMock()
    storage_manager.get_proxy_and_volume.return_value = ("local", "volume1")  # type: ignore[attr-defined]
    storage_manager.get_manager_facing_client.return_value = mock_client  # type: ignore[attr-defined]

    clone_response = MagicMock()
    clone_response.bgtask_id = TaskID(uuid.uuid4())
    mock_client.clone_folder.return_value = clone_response

    return mock_client


@pytest.fixture()
async def set_main_access_key(
    db_engine: SAEngine,
    admin_user_fixture: Any,
) -> AsyncIterator[None]:
    """Populate main_access_key on the admin user so that the
    ``main_keypair`` ORM relationship resolves correctly.

    The global ``admin_user_fixture`` does not set this column, but the
    clone flow needs it to look up ``allowed_vfolder_hosts`` from the
    user's keypair resource policy.
    """
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(users)
            .where(users.c.uuid == str(admin_user_fixture.user_uuid))
            .values(main_access_key=admin_user_fixture.keypair.access_key)
        )
    yield
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(users)
            .where(users.c.uuid == str(admin_user_fixture.user_uuid))
            .values(main_access_key=None)
        )


@pytest.fixture()
async def cloneable_project_vfolder(
    vfolder_factory: VFolderFactory,
    admin_user_fixture: Any,
    group_fixture: uuid.UUID,
) -> VFolderFixtureData:
    """A cloneable project-owned vfolder as the clone source."""
    return await vfolder_factory(
        name="project-source-clone",
        cloneable=True,
        ownership_type=VFolderOwnershipType.GROUP,
        group=str(group_fixture),
        user=str(admin_user_fixture.user_uuid),
        quota_scope_id=str(QuotaScopeID(scope_type=QuotaScopeType.PROJECT, scope_id=group_fixture)),
    )


@pytest.fixture()
async def user_policy_capped_at_1(
    db_engine: SAEngine,
    resource_policy_fixture: str,
) -> AsyncIterator[None]:
    """Set user max_vfolder_count=1 and project max_vfolder_count=100."""
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(UserResourcePolicyRow.__table__)
            .where(UserResourcePolicyRow.__table__.c.name == resource_policy_fixture)
            .values(max_vfolder_count=1)
        )
        await conn.execute(
            sa.update(ProjectResourcePolicyRow.__table__)
            .where(ProjectResourcePolicyRow.__table__.c.name == resource_policy_fixture)
            .values(max_vfolder_count=100)
        )
    yield
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(UserResourcePolicyRow.__table__)
            .where(UserResourcePolicyRow.__table__.c.name == resource_policy_fixture)
            .values(max_vfolder_count=0)
        )
        await conn.execute(
            sa.update(ProjectResourcePolicyRow.__table__)
            .where(ProjectResourcePolicyRow.__table__.c.name == resource_policy_fixture)
            .values(max_vfolder_count=0)
        )


@pytest.fixture()
async def user_policy_unlimited_project_capped_at_1(
    db_engine: SAEngine,
    resource_policy_fixture: str,
) -> AsyncIterator[None]:
    """Set user max_vfolder_count=0 (unlimited) and project max_vfolder_count=1."""
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(UserResourcePolicyRow.__table__)
            .where(UserResourcePolicyRow.__table__.c.name == resource_policy_fixture)
            .values(max_vfolder_count=0)
        )
        await conn.execute(
            sa.update(ProjectResourcePolicyRow.__table__)
            .where(ProjectResourcePolicyRow.__table__.c.name == resource_policy_fixture)
            .values(max_vfolder_count=1)
        )
    yield
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(ProjectResourcePolicyRow.__table__)
            .where(ProjectResourcePolicyRow.__table__.c.name == resource_policy_fixture)
            .values(max_vfolder_count=0)
        )


# ---------------------------------------------------------------------------
# v1 clone tests (POST /folders/{name}/clone)
# ---------------------------------------------------------------------------


class TestVFolderClonePolicyCheck:
    """Clone must enforce the *requester's user* resource policy, not the source project's."""

    async def test_clone_project_vfolder_blocked_by_user_policy(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        set_main_access_key: None,
        user_policy_capped_at_1: None,
        cloneable_project_vfolder: VFolderFixtureData,
    ) -> None:
        """Cloning a project vfolder should fail when the user's max_vfolder_count is reached.

        Setup:
          - user  resource policy: max_vfolder_count = 1
          - project resource policy: max_vfolder_count = 100  (would NOT block if used)
          - 1 existing user-owned vfolder  (hits the user limit)
          - 1 cloneable project-owned vfolder (the source)

        If the code incorrectly checked the project policy (max=100), the clone
        would succeed.  The correct behaviour is to reject it because the user
        already owns 1 vfolder and the user policy only allows 1.
        """
        await vfolder_factory(name="user-vf-occupying-slot")

        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.vfolder.clone(
                cloneable_project_vfolder["name"],
                CloneVFolderReq(target_name="cloned-should-fail"),
            )
        assert exc_info.value.status == 400

    async def test_clone_project_vfolder_allowed_by_user_policy(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        set_main_access_key: None,
        user_policy_unlimited_project_capped_at_1: None,
        cloneable_project_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """Cloning a project vfolder should succeed when the user's policy allows it,
        even if the project's max_vfolder_count would block (if it were used).

        Setup:
          - user  resource policy: max_vfolder_count = 0  (unlimited)
          - project resource policy: max_vfolder_count = 1  (would block if used)
          - 2 existing user-owned vfolders  (would exceed project limit of 1)
          - 1 cloneable project-owned vfolder (the source)

        If the code incorrectly checked the project policy (max=1), the clone
        would fail.  The correct behaviour is to allow it because the user policy
        is unlimited (max=0).
        """
        _configure_clone_storage_mock(storage_manager)

        await vfolder_factory(name="user-vf-1-clone-ok")
        await vfolder_factory(name="user-vf-2-clone-ok")

        result = await admin_registry.vfolder.clone(
            cloneable_project_vfolder["name"],
            CloneVFolderReq(target_name="cloned-should-succeed"),
        )
        assert result.root.name == "cloned-should-succeed"


# ---------------------------------------------------------------------------
# v1 clone response format (BA-4879)
# ---------------------------------------------------------------------------


class TestVFolderCloneResponseFormat:
    """Clone response must be flat JSON without an 'item' wrapper (BA-4879)."""

    async def test_clone_response_is_flat_json(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        set_main_access_key: None,
        user_policy_unlimited_project_capped_at_1: None,
        cloneable_project_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """The clone endpoint must return a flat dict with bgtask_id at the
        top level, not wrapped in {"item": {...}}.

        Regression test for BA-4879: VFolderCloneResponse was using
        BaseResponseModel (which wraps as {"item": {...}}) instead of
        BaseRootResponseModel (flat JSON).
        """
        _configure_clone_storage_mock(storage_manager)

        source_name = cloneable_project_vfolder["name"]
        raw = await admin_registry._client._request(
            "POST",
            f"/folders/{source_name}/clone",
            json={"target_name": "clone-format-test"},
        )
        assert isinstance(raw, dict)
        # Must NOT have an "item" wrapper
        assert "item" not in raw
        # Fields must be at top level
        assert "bgtask_id" in raw
        assert "name" in raw
        assert raw["name"] == "clone-format-test"


# ---------------------------------------------------------------------------
# v2 clone tests (POST /v2/vfolders/{vfolder_id}/clone)
# ---------------------------------------------------------------------------


class TestVFolderCloneV2PolicyCheck:
    """clone_v2 must enforce the *requester's user* resource policy, not the source project's."""

    async def test_clone_v2_project_vfolder_blocked_by_user_policy(
        self,
        admin_v2_registry: V2ClientRegistry,
        vfolder_factory: VFolderFactory,
        set_main_access_key: None,
        user_policy_capped_at_1: None,
        cloneable_project_vfolder: VFolderFixtureData,
    ) -> None:
        """v2 clone of a project vfolder should fail when the user's max_vfolder_count is reached."""
        await vfolder_factory(name="user-vf-occupying-slot-v2")

        with pytest.raises(BackendAPIError) as exc_info:
            await admin_v2_registry.vfolder.clone(
                cloneable_project_vfolder["id"],
                CloneVFolderInput(name="cloned-v2-should-fail"),
            )
        assert exc_info.value.status == 400

    async def test_clone_v2_project_vfolder_allowed_by_user_policy(
        self,
        admin_v2_registry: V2ClientRegistry,
        vfolder_factory: VFolderFactory,
        set_main_access_key: None,
        user_policy_unlimited_project_capped_at_1: None,
        cloneable_project_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """v2 clone of a project vfolder should succeed when the user's policy allows it."""
        _configure_clone_storage_mock(storage_manager)

        await vfolder_factory(name="user-vf-1-clone-ok-v2")
        await vfolder_factory(name="user-vf-2-clone-ok-v2")

        result = await admin_v2_registry.vfolder.clone(
            cloneable_project_vfolder["id"],
            CloneVFolderInput(name="cloned-v2-should-succeed"),
        )
        assert result.vfolder.metadata.name == "cloned-v2-should-succeed"
