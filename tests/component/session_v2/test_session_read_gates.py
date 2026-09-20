"""Component tests for the gates on session and kernel reads.

- A project's sessions are read on the project scope, not the caller's user scope.
- A session's kernels are read on that session.
- The sessions and kernels under an agent are superadmin-only.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Iterator, Sequence
from typing import TYPE_CHECKING, Any

import pytest
import sqlalchemy as sa

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission, RoleStatus
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import ProcessorDependencies
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
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.kernel.searchers import KernelSearcher
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.session.searchers import SessionSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.session.actions.global_search import GlobalSearchSessionsAction
from ai.backend.manager.services.session.actions.global_search_kernels import (
    GlobalSearchKernelsAction,
)
from ai.backend.manager.services.session.actions.scoped_search_kernels import (
    ScopedSearchKernelsAction,
)
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
    from tests.component.conftest import UserFixtureData

    from .conftest import SessionSeedData


@pytest.fixture()
def processor_registry(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> ProcessorRegistry[Any]:
    """The shared registry with the RBAC validators the gates under test run."""
    permission_repo = RbacPermissionCheckRepository(
        PermissionOpsProvider(database_engine), config_provider
    )
    validators = VirtualEntityRBACValidators(
        scope=VirtualEntityScopeActionRBACValidator(permission_repo, config_provider),
        single_entity=VirtualEntitySingleEntityActionRBACValidator(
            permission_repo, config_provider
        ),
        partial_bulk=VirtualEntityPartialBulkActionRBACValidator(permission_repo),
        atomic_bulk=VirtualEntityAtomicBulkActionRBACValidator(permission_repo),
        relation=VirtualEntityRelationActionRBACValidator(permission_repo, config_provider),
    )
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=validators.to_action_validators(),
            repository=OpsRepository(V2DBOpsProvider(database_engine)),
        )
    )


async def _place_session(
    db_engine: SAEngine,
    session_id: SessionID,
    scopes: Sequence[tuple[EntityType, uuid.UUID]],
) -> None:
    """Write the graph rows session creation writes: each scope owns and governs it."""
    ve = VirtualEntityRow.__table__
    async with db_engine.begin() as conn:
        node_id = uuid.uuid4()
        await conn.execute(
            sa.insert(ve).values(id=node_id, entity_type=SessionEntityType(), entity_id=session_id)
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
        for scope_type, scope_id in scopes:
            scope_node_id = (
                await conn.execute(
                    sa.select(ve.c.id).where(
                        ve.c.entity_type == scope_type, ve.c.entity_id == scope_id
                    )
                )
            ).scalar_one()
            await conn.execute(
                sa.insert(EntityMembershipRow.__table__).values(
                    virtual_entity_id=scope_node_id, member_entity_id=node_id, capped=False
                )
            )
            await conn.execute(
                sa.insert(ScopeBindingRow.__table__).values(
                    virtual_entity_id=node_id, scope_entity_id=scope_node_id, permission_cap=None
                )
            )


async def _unplace_session(db_engine: SAEngine, session_id: SessionID) -> None:
    ve = VirtualEntityRow.__table__
    async with db_engine.begin() as conn:
        await conn.execute(
            ve.delete().where(ve.c.entity_type == SessionEntityType(), ve.c.entity_id == session_id)
        )


@pytest.fixture()
async def placed_user_session(
    db_engine: SAEngine,
    user_session_seed: SessionSeedData,
    group_fixture: uuid.UUID,
) -> AsyncIterator[SessionSeedData]:
    """The regular user's session, in the user and project scopes."""
    assert user_session_seed.user_uuid is not None
    await _place_session(
        db_engine,
        user_session_seed.session_id,
        [(UserEntityType(), user_session_seed.user_uuid), (ProjectEntityType(), group_fixture)],
    )
    yield user_session_seed
    await _unplace_session(db_engine, user_session_seed.session_id)


@pytest.fixture()
async def placed_admin_session(
    db_engine: SAEngine,
    admin_session_seed: SessionSeedData,
    group_fixture: uuid.UUID,
) -> AsyncIterator[SessionSeedData]:
    """The admin's session, in the admin's user scope and the project scope."""
    assert admin_session_seed.user_uuid is not None
    await _place_session(
        db_engine,
        admin_session_seed.session_id,
        [(UserEntityType(), admin_session_seed.user_uuid), (ProjectEntityType(), group_fixture)],
    )
    yield admin_session_seed
    await _unplace_session(db_engine, admin_session_seed.session_id)


@pytest.fixture()
async def project_session_reader_role(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[uuid.UUID]:
    """A project-scope role granting session READ, assigned to the regular user."""
    role_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name=f"project-session-reader-{role_id.hex[:8]}",
                status=RoleStatus.ACTIVE,
                scope_type=ProjectEntityType(),
                scope_id=group_fixture,
            )
        )
        await conn.execute(
            sa.insert(UserRoleRow.__table__).values(
                user_id=regular_user_fixture.user_uuid, role_id=role_id
            )
        )
        await conn.execute(
            sa.insert(PermissionRow.__table__).values(
                role_id=role_id, entity_type=SessionEntityType(), permission=Permission.READ
            )
        )
    yield role_id
    async with db_engine.begin() as conn:
        await conn.execute(
            PermissionRow.__table__.delete().where(PermissionRow.__table__.c.role_id == role_id)
        )
        await conn.execute(
            UserRoleRow.__table__.delete().where(UserRoleRow.__table__.c.role_id == role_id)
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id == role_id))


@pytest.fixture()
def regular_user_context(
    regular_user_fixture: UserFixtureData,
    domain_fixture: DomainFixtureData,
) -> Iterator[None]:
    with with_user(
        UserData(
            user_id=regular_user_fixture.user_uuid,
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name=domain_fixture.domain_name,
            domain_id=domain_fixture.domain_id,
        )
    ):
        yield


@pytest.fixture()
def superadmin_context(
    admin_user_fixture: UserFixtureData,
    domain_fixture: DomainFixtureData,
) -> Iterator[None]:
    with with_user(
        UserData(
            user_id=admin_user_fixture.user_uuid,
            is_authorized=True,
            is_admin=True,
            is_superadmin=True,
            role=UserRole.SUPERADMIN,
            domain_name=domain_fixture.domain_name,
            domain_id=domain_fixture.domain_id,
        )
    ):
        yield


class TestProjectSessionSearchGate:
    """POST /v2/sessions/projects/{project_id}/search is gated on the project scope."""

    async def test_user_scope_permission_does_not_reach_project(
        self,
        user_v2_registry: V2ClientRegistry,
        placed_user_session: SessionSeedData,
        group_fixture: uuid.UUID,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.session.project_search(group_fixture, AdminSearchSessionsInput())

    async def test_project_permission_reads_project_sessions(
        self,
        user_v2_registry: V2ClientRegistry,
        placed_user_session: SessionSeedData,
        placed_admin_session: SessionSeedData,
        project_session_reader_role: uuid.UUID,
        group_fixture: uuid.UUID,
    ) -> None:
        result = await user_v2_registry.session.project_search(
            group_fixture, AdminSearchSessionsInput()
        )
        found = {item.id for item in result.items}
        assert found == {placed_user_session.session_id, placed_admin_session.session_id}


@pytest.mark.usefixtures("regular_user_context")
class TestSessionKernelSearchGate:
    """The kernels of a session are read on that session."""

    async def test_owned_session_kernels_are_read(
        self,
        session_processors: SessionProcessors,
        placed_user_session: SessionSeedData,
    ) -> None:
        result = await session_processors.scoped_search_kernels.run(
            ScopedSearchKernelsAction(
                session_ids=[placed_user_session.session_id],
                searcher=KernelSearcher(pagination=NoPagination()),
            )
        )
        assert [item.id for item in result.items] == [placed_user_session.kernel_id]

    async def test_unowned_session_kernels_are_refused(
        self,
        session_processors: SessionProcessors,
        user_system_role: uuid.UUID,
        placed_admin_session: SessionSeedData,
    ) -> None:
        with pytest.raises(NotEnoughPermission):
            await session_processors.scoped_search_kernels.run(
                ScopedSearchKernelsAction(
                    session_ids=[placed_admin_session.session_id],
                    searcher=KernelSearcher(pagination=NoPagination()),
                )
            )


class TestAgentChildSearchGate:
    """The sessions and kernels under an agent are read through the global searches."""

    @pytest.mark.usefixtures("regular_user_context")
    async def test_regular_user_is_refused_sessions(
        self,
        session_processors: SessionProcessors,
        user_system_role: uuid.UUID,
    ) -> None:
        with pytest.raises(InsufficientPrivilege):
            await session_processors.global_search.run(
                GlobalSearchSessionsAction(
                    searcher=GlobalSearcher(
                        used_by=(), searcher=SessionSearcher(pagination=NoPagination())
                    )
                )
            )

    @pytest.mark.usefixtures("regular_user_context")
    async def test_regular_user_is_refused_kernels(
        self,
        session_processors: SessionProcessors,
        user_system_role: uuid.UUID,
    ) -> None:
        with pytest.raises(InsufficientPrivilege):
            await session_processors.global_search_kernels.run(
                GlobalSearchKernelsAction(
                    searcher=GlobalSearcher(
                        used_by=(), searcher=KernelSearcher(pagination=NoPagination())
                    )
                )
            )

    @pytest.mark.usefixtures("superadmin_context")
    async def test_superadmin_reads_sessions_and_kernels(
        self,
        session_processors: SessionProcessors,
        user_session_seed: SessionSeedData,
    ) -> None:
        sessions = await session_processors.global_search.run(
            GlobalSearchSessionsAction(
                searcher=GlobalSearcher(
                    used_by=(), searcher=SessionSearcher(pagination=NoPagination())
                )
            )
        )
        kernels = await session_processors.global_search_kernels.run(
            GlobalSearchKernelsAction(
                searcher=GlobalSearcher(
                    used_by=(), searcher=KernelSearcher(pagination=NoPagination())
                )
            )
        )
        assert user_session_seed.session_id in {item.id for item in sessions.items}
        assert user_session_seed.kernel_id in {item.id for item in kernels.items}


class TestMySessionSearchGate:
    """POST /v2/sessions/my/search reads the sessions the caller's user scope reaches."""

    async def test_returns_sessions_in_caller_user_scope(
        self,
        user_v2_registry: V2ClientRegistry,
        placed_user_session: SessionSeedData,
        placed_admin_session: SessionSeedData,
    ) -> None:
        result = await user_v2_registry.session.my_search(AdminSearchSessionsInput())
        assert [item.id for item in result.items] == [placed_user_session.session_id]

    async def test_owner_column_alone_is_not_membership(
        self,
        user_v2_registry: V2ClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        result = await user_v2_registry.session.my_search(AdminSearchSessionsInput())
        assert result.items == []
