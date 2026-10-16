"""Relation and roster seed items go through the primitives their API uses, after the
entity items, and a written user or project is lent the resource policies it is subject
to."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.resource_group import (
    ResourceGroupEntityType,
    ResourceGroupID,
)
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    ProjectResourcePolicyEntityType,
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.errors.resource import (
    PersonalProjectMemberAdditionError,
    ProjectMemberNotJoinableError,
)
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_group.creators import (
    ResourceGroupForProjectRelationCreator,
)
from ai.backend.manager.models.resource_group.row import ResourceGroupForProjectRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.seed.types import (
    SeedItemWrite,
    SeedRelationWrite,
    SeedRosterWrite,
    SeedWriteItemResult,
)
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.domain.seed import DomainSeed
from ai.backend.manager.seed.project.seed import ProjectSeed
from ai.backend.manager.seed.resource_group.seed import ResourceGroupSeed
from ai.backend.manager.seed.resource_policy.seed import (
    KeyPairResourcePolicySeed,
    ProjectResourcePolicySeed,
    UserResourcePolicySeed,
)
from ai.backend.manager.seed.user.seed import UserSeed
from ai.backend.testutils.db import with_tables

_DOMAIN = DomainID(uuid.UUID("0198a5a0-0000-7000-8000-0000000a0001"))
_OTHER_DOMAIN = DomainID(uuid.UUID("0198a5a0-0000-7000-8000-0000000a0002"))
_USER_POLICY = uuid.UUID("0198a5a0-0000-7000-8000-0000000b0001")
_PROJECT_POLICY = uuid.UUID("0198a5a0-0000-7000-8000-0000000b0002")
_KEYPAIR_POLICY = uuid.UUID("0198a5a0-0000-7000-8000-0000000b0003")
_MEMBER = UserID(uuid.UUID("0198a5a0-0000-7000-8000-0000000c0001"))
_OUTSIDER = UserID(uuid.UUID("0198a5a0-0000-7000-8000-0000000c0002"))
_PROJECT = ProjectID(uuid.UUID("0198a5a0-0000-7000-8000-0000000d0001"))
_PERSONAL = ProjectID(uuid.UUID("0198a5a0-0000-7000-8000-0000000d0002"))
_RESOURCE_GROUP = ResourceGroupID(uuid.UUID("0198a5a0-0000-7000-8000-0000000e0001"))
_OTHER_RESOURCE_GROUP = ResourceGroupID(uuid.UUID("0198a5a0-0000-7000-8000-0000000e0002"))


def _user(user_id: UserID, domain_id: DomainID, name: str) -> UserSeed:
    return UserSeed.model_validate({
        "id": str(user_id),
        "domain_id": str(domain_id),
        "email": f"{name}@example.com",
        "username": name,
        "password": f"{name}-password",
        "resource_policy": "default",
        "keypairs": [
            {
                "access_key": f"AKIA{name.upper():0<16}"[:20],
                "secret_key": f"{name}-secret",
                "is_default": True,
                "resource_policy": "default",
            }
        ],
    })


def _project(project_id: ProjectID, name: str, **values: Any) -> ProjectSeed:
    return ProjectSeed.model_validate({
        "id": str(project_id),
        "domain_id": str(_DOMAIN),
        "name": name,
        "resource_policy": "default",
        **values,
    })


def _resource_group(resource_group_id: ResourceGroupID, name: str) -> ResourceGroupSeed:
    return ResourceGroupSeed.model_validate({
        "id": str(resource_group_id),
        "name": name,
        "driver": "static",
        "scheduler": "fifo",
    })


def _entities() -> list[SeedItemWrite]:
    """The entities the relation and roster items name, in kind order."""
    return [
        UserResourcePolicySeed.model_validate({
            "uuid": str(_USER_POLICY),
            "name": "default",
            "max_vfolder_count": 0,
            "max_quota_scope_size": -1,
            "max_session_count_per_model_session": 10,
        }).write(),
        ProjectResourcePolicySeed.model_validate({
            "uuid": str(_PROJECT_POLICY),
            "name": "default",
            "max_vfolder_count": 0,
            "max_quota_scope_size": -1,
            "max_network_count": 3,
        }).write(),
        KeyPairResourcePolicySeed.model_validate({
            "uuid": str(_KEYPAIR_POLICY),
            "name": "default",
            "total_resource_slots": {},
            "max_concurrent_sessions": 5,
            "max_containers_per_session": 1,
            "idle_timeout": 3600,
            "max_pending_session_resource_slots": {},
            "allowed_vfolder_hosts": {},
        }).write(),
        DomainSeed.model_validate({"id": str(_DOMAIN), "name": "default"}).write(),
        DomainSeed.model_validate({"id": str(_OTHER_DOMAIN), "name": "other"}).write(),
        _user(_MEMBER, _DOMAIN, "member").write(),
        _user(_OUTSIDER, _OTHER_DOMAIN, "outsider").write(),
        _project(_PROJECT, "research").write(),
        _project(_PERSONAL, "personal", type="personal", creator_id=str(_MEMBER)).write(),
        _resource_group(_RESOURCE_GROUP, "default").write(),
        _resource_group(_OTHER_RESOURCE_GROUP, "gpu").write(),
    ]


def _allow(project_id: ProjectID, resource_group_id: ResourceGroupID) -> SeedRelationWrite:
    return SeedRelationWrite(
        creator=ResourceGroupForProjectRelationCreator(),
        scope=project_id,
        target=resource_group_id,
    )


def _node(entity_type: EntityType, entity_id: uuid.UUID) -> sa.ScalarSelect[Any]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(VirtualEntityRow.entity_type == entity_type, VirtualEntityRow.entity_id == entity_id)
        .scalar_subquery()
    )


def _membership(
    scope_type: EntityType, scope_id: uuid.UUID, member_type: EntityType, member_id: uuid.UUID
) -> sa.Select[Any]:
    return sa.select(EntityMembershipRow.id).where(
        EntityMembershipRow.virtual_entity_id == _node(scope_type, scope_id),
        EntityMembershipRow.member_entity_id == _node(member_type, member_id),
    )


def _govern(project_id: ProjectID, resource_group_id: ResourceGroupID) -> sa.Select[Any]:
    return sa.select(ScopeBindingRow.permission_cap).where(
        ScopeBindingRow.virtual_entity_id == _node(ResourceGroupEntityType(), resource_group_id),
        ScopeBindingRow.scope_entity_id == _node(ProjectEntityType(), project_id),
    )


async def _scalars(db: ExtendedAsyncSAEngine, stmt: sa.Select[Any]) -> list[Any]:
    async with db.begin_readonly() as conn:
        return list((await conn.scalars(stmt)).all())


async def _allowed_rows(db: ExtendedAsyncSAEngine) -> list[uuid.UUID]:
    return await _scalars(db, sa.select(ResourceGroupForProjectRow.id))


@pytest.fixture
async def relation_db(db: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(db, [ResourceGroupForProjectRow]):
        yield db


@pytest.fixture
async def entities(relation_db: ExtendedAsyncSAEngine, repository: SeedRepository) -> None:
    results = await repository.partial_write(_entities(), overwrite=False)
    assert all(result.error is None for result in results), results


class TestRelation:
    async def test_a_relation_is_linked_with_its_graph_reads(
        self, relation_db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        results = await repository.partial_write(
            [_allow(_PROJECT, _RESOURCE_GROUP)], overwrite=False
        )

        assert results == [SeedWriteItemResult(written=True)]
        assert len(await _allowed_rows(relation_db)) == 1
        assert await _scalars(relation_db, _govern(_PROJECT, _RESOURCE_GROUP)) == [Permission.READ]
        shared = _membership(
            ResourceGroupEntityType(), _RESOURCE_GROUP, ProjectEntityType(), _PROJECT
        )
        assert len(await _scalars(relation_db, shared)) == 1

    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_applying_again_leaves_the_rows_as_they_are(
        self,
        relation_db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        entities: None,
        overwrite: bool,
    ) -> None:
        await repository.partial_write([_allow(_PROJECT, _RESOURCE_GROUP)], overwrite=False)
        rows = await _allowed_rows(relation_db)
        shared = _membership(
            ResourceGroupEntityType(), _RESOURCE_GROUP, ProjectEntityType(), _PROJECT
        )
        shares = await _scalars(relation_db, shared)

        results = await repository.partial_write(
            [_allow(_PROJECT, _RESOURCE_GROUP)], overwrite=overwrite
        )

        assert results == [SeedWriteItemResult(written=False)]
        assert await _allowed_rows(relation_db) == rows
        assert await _scalars(relation_db, shared) == shares

    async def test_applying_again_fills_the_graph_reads_a_row_is_missing(
        self, relation_db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        await repository.partial_write([_allow(_PROJECT, _RESOURCE_GROUP)], overwrite=False)
        async with relation_db.begin_session() as sess:
            await sess.execute(
                sa.delete(ScopeBindingRow).where(
                    ScopeBindingRow.virtual_entity_id
                    == _node(ResourceGroupEntityType(), _RESOURCE_GROUP),
                    ScopeBindingRow.scope_entity_id == _node(ProjectEntityType(), _PROJECT),
                )
            )

        results = await repository.partial_write(
            [_allow(_PROJECT, _RESOURCE_GROUP)], overwrite=False
        )

        assert results == [SeedWriteItemResult(written=False)]
        assert await _scalars(relation_db, _govern(_PROJECT, _RESOURCE_GROUP)) == [Permission.READ]

    async def test_a_relation_naming_a_missing_entity_fails_alone(
        self, relation_db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        missing = ResourceGroupID(uuid.uuid4())
        results = await repository.partial_write(
            [
                _allow(_PROJECT, _RESOURCE_GROUP),
                _allow(_PROJECT, missing),
                _allow(_PROJECT, _OTHER_RESOURCE_GROUP),
            ],
            overwrite=False,
        )

        assert [result.written for result in results] == [True, False, True]
        assert isinstance(results[1].error, ForeignKeyViolationError)
        assert len(await _allowed_rows(relation_db)) == 2


class TestRoster:
    @pytest.fixture
    async def auto_assign_role(self, relation_db: ExtendedAsyncSAEngine, entities: None) -> RoleID:
        role_id = RoleID(uuid.uuid4())
        async with relation_db.begin_session() as sess:
            sess.add(
                RoleRow(
                    id=role_id,
                    name="research-member",
                    auto_assign=True,
                    scope_type=ProjectEntityType(),
                    scope_id=_PROJECT,
                )
            )
        return role_id

    async def _roles_of(self, db: ExtendedAsyncSAEngine, user_id: UserID) -> list[uuid.UUID]:
        return await _scalars(
            db, sa.select(UserRoleRow.role_id).where(UserRoleRow.user_id == user_id)
        )

    def _place(self) -> sa.Select[Any]:
        return _membership(ProjectEntityType(), _PROJECT, UserEntityType(), _MEMBER)

    async def test_a_user_joins_with_the_auto_assign_roles(
        self,
        relation_db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        auto_assign_role: RoleID,
    ) -> None:
        results = await repository.partial_write(
            [SeedRosterWrite(project_id=_PROJECT, user_id=_MEMBER)], overwrite=False
        )

        assert results == [SeedWriteItemResult(written=True)]
        assert len(await _scalars(relation_db, self._place())) == 1
        assert await self._roles_of(relation_db, _MEMBER) == [auto_assign_role]

    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_a_member_already_on_the_roster_is_left_as_it_stands(
        self,
        relation_db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        auto_assign_role: RoleID,
        overwrite: bool,
    ) -> None:
        member = SeedRosterWrite(project_id=_PROJECT, user_id=_MEMBER)
        await repository.partial_write([member], overwrite=False)
        place = await _scalars(relation_db, self._place())

        results = await repository.partial_write([member], overwrite=overwrite)

        assert results == [SeedWriteItemResult(written=False)]
        assert await _scalars(relation_db, self._place()) == place

    @pytest.mark.parametrize(
        ("project_id", "user_id", "error"),
        [
            (_PERSONAL, _MEMBER, PersonalProjectMemberAdditionError),
            (_PROJECT, _OUTSIDER, ProjectMemberNotJoinableError),
            (_PROJECT, UserID(uuid.uuid4()), ProjectMemberNotJoinableError),
        ],
        ids=["personal-project", "other-domain", "missing-user"],
    )
    async def test_a_place_the_roster_refuses_fails_alone(
        self,
        relation_db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        auto_assign_role: RoleID,
        project_id: ProjectID,
        user_id: UserID,
        error: type[Exception],
    ) -> None:
        results = await repository.partial_write(
            [
                SeedRosterWrite(project_id=project_id, user_id=user_id),
                SeedRosterWrite(project_id=_PROJECT, user_id=_MEMBER),
            ],
            overwrite=False,
        )

        assert [result.written for result in results] == [False, True]
        assert isinstance(results[0].error, error)


class TestResourcePolicyShare:
    async def test_a_written_user_and_project_are_lent_their_policies(
        self, relation_db: ExtendedAsyncSAEngine, entities: None
    ) -> None:
        lent = [
            _membership(UserEntityType(), _MEMBER, UserResourcePolicyEntityType(), _USER_POLICY),
            _membership(
                UserEntityType(), _MEMBER, KeyPairResourcePolicyEntityType(), _KEYPAIR_POLICY
            ),
            _membership(
                ProjectEntityType(), _PROJECT, ProjectResourcePolicyEntityType(), _PROJECT_POLICY
            ),
        ]
        for share in lent:
            assert len(await _scalars(relation_db, share)) == 1

    async def test_applying_again_keeps_the_share(
        self, relation_db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        share = _membership(UserEntityType(), _MEMBER, UserResourcePolicyEntityType(), _USER_POLICY)
        before = await _scalars(relation_db, share)

        await repository.partial_write(_entities(), overwrite=False)

        assert await _scalars(relation_db, share) == before

    async def test_overwrite_restates_a_share_that_was_dropped(
        self, relation_db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        share = _membership(
            ProjectEntityType(), _PROJECT, ProjectResourcePolicyEntityType(), _PROJECT_POLICY
        )
        async with relation_db.begin_session() as sess:
            await sess.execute(
                sa.delete(EntityMembershipRow).where(EntityMembershipRow.id.in_(share))
            )

        await repository.partial_write(_entities(), overwrite=True)

        assert len(await _scalars(relation_db, share)) == 1
