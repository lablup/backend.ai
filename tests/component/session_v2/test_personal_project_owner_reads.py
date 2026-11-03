"""What a newly created user reads through the roles the declared presets give them."""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import TYPE_CHECKING, Any

import pytest
import sqlalchemy as sa

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.ops.v2.user.provider import UserOpsProvider
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
    from tests.component.conftest import KeypairFixtureData, ProvisionedUserData

type ProvisionUser = Callable[[], Coroutine[Any, Any, ProvisionedUserData]]
type PlaceSession = Callable[[ProvisionedUserData], Coroutine[Any, Any, SessionID]]
type RegistryFor = Callable[[KeypairFixtureData], Coroutine[Any, Any, V2ClientRegistry]]


@pytest.fixture()
def processor_registry(rbac_processor_registry: ProcessorRegistry[Any]) -> ProcessorRegistry[Any]:
    return rbac_processor_registry


@pytest.fixture()
async def owner(provision_user: ProvisionUser) -> ProvisionedUserData:
    return await provision_user()


@pytest.fixture()
async def other_user(provision_user: ProvisionUser) -> ProvisionedUserData:
    return await provision_user()


@pytest.fixture()
async def owner_registry(
    v2_registry_for: RegistryFor,
    owner: ProvisionedUserData,
) -> V2ClientRegistry:
    return await v2_registry_for(owner.keypair)


@pytest.fixture()
async def owned_session(
    place_personal_session: PlaceSession,
    owner: ProvisionedUserData,
) -> SessionID:
    return await place_personal_session(owner)


@pytest.fixture()
async def session_shared_to_owner(
    database_engine: ExtendedAsyncSAEngine,
    place_personal_session: PlaceSession,
    owner: ProvisionedUserData,
    other_user: ProvisionedUserData,
) -> SessionID:
    """Another user's session in the owner's personal project under a READ cap, where
    accepting a share lands it."""
    session_id = await place_personal_session(other_user)
    async with ShareOpsProvider(database_engine).write_ops() as w:
        await w.replace_share(owner.personal_project_id, session_id, Permission.READ)
    return session_id


@pytest.fixture()
async def team_project(
    database_engine: ExtendedAsyncSAEngine,
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
    declared_role_presets: list[uuid.UUID],
) -> AsyncIterator[ProjectID]:
    """A general project created the way every project is, so it holds its preset roles."""
    async with UserOpsProvider(database_engine).write_ops() as w:
        project = await w.create_role_managed_entity(
            ProjectCreator(
                name=f"team-{secrets.token_hex(4)}",
                domain_id=DomainID(domain_fixture.domain_id),
                domain_name=domain_fixture.domain_name,
                type=ProjectType.GENERAL,
                resource_policy=resource_policy_fixture,
            )
        )
    project_id = ProjectID(project.id)
    yield project_id
    roles = RoleRow.__table__
    ve = VirtualEntityRow.__table__
    async with db_engine.begin() as conn:
        role_ids = (
            (
                await conn.execute(
                    sa.select(roles.c.id).where(
                        roles.c.scope_type == ProjectEntityType(),
                        roles.c.scope_id == project_id,
                    )
                )
            )
            .scalars()
            .all()
        )
        await conn.execute(
            ve.delete().where(
                sa.or_(
                    sa.and_(ve.c.entity_type == RoleEntityType(), ve.c.entity_id.in_(role_ids)),
                    sa.and_(ve.c.entity_type == ProjectEntityType(), ve.c.entity_id == project_id),
                )
            )
        )
        await conn.execute(roles.delete().where(roles.c.id.in_(role_ids)))
        await conn.execute(
            ProjectRow.__table__.delete().where(ProjectRow.__table__.c.id == project_id)
        )


@pytest.fixture()
async def owner_on_team_project(
    database_engine: ExtendedAsyncSAEngine,
    domain_fixture: DomainFixtureData,
    owner: ProvisionedUserData,
    team_project: ProjectID,
) -> ProjectID:
    async with UserOpsProvider(database_engine).write_ops() as w:
        await w.join_projects(owner.user_id, DomainID(domain_fixture.domain_id), [team_project])
    return team_project


class TestPersonalProjectOwnerReads:
    async def test_owner_searches_sessions_in_their_personal_project(
        self,
        owner_registry: V2ClientRegistry,
        owner: ProvisionedUserData,
        owned_session: SessionID,
    ) -> None:
        payload = await owner_registry.session.project_search(
            owner.personal_project_id, AdminSearchSessionsInput()
        )
        assert [str(node.id) for node in payload.items] == [str(owned_session)]

    async def test_my_search_includes_a_session_shared_to_the_owner(
        self,
        owner_registry: V2ClientRegistry,
        session_shared_to_owner: SessionID,
    ) -> None:
        payload = await owner_registry.session.my_search(AdminSearchSessionsInput())
        assert [str(node.id) for node in payload.items] == [str(session_shared_to_owner)]

    async def test_another_users_personal_project_is_refused(
        self,
        owner_registry: V2ClientRegistry,
        other_user: ProvisionedUserData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await owner_registry.session.project_search(
                other_user.personal_project_id, AdminSearchSessionsInput()
            )

    async def test_a_team_project_member_is_refused(
        self,
        owner_registry: V2ClientRegistry,
        owner_on_team_project: ProjectID,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await owner_registry.session.project_search(
                owner_on_team_project, AdminSearchSessionsInput()
            )
