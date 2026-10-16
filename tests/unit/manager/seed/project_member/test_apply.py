"""`mgr seed apply` puts the project member files on the roster the way the roster API
joins a user."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.errors.resource import (
    PersonalProjectMemberAdditionError,
    ProjectMemberNotJoinableError,
    ProjectNotFound,
)
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWriteItemResult
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.project.seed import ProjectSeed
from ai.backend.manager.seed.project_member.seed import ProjectMemberSeed
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

# A user's place on a project: the caps of the roster edge and the project's roles held.
type _Place = tuple[set[tuple[str, bool]], set[uuid.UUID]]


@pytest.fixture
def plan(project_member_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([project_member_seed_dir])


@pytest.fixture
async def applied(repository: SeedRepository, plan: SeedPlan) -> None:
    """The member files applied, with the projects, users and roles they refer to."""
    await SeedApplier(repository).apply(plan, overwrite=False)


@pytest.fixture
def research_admin(plan: SeedPlan, research_project_id: str) -> ProjectMemberSeed:
    [seed] = [seed for seed in _seeds(plan) if str(seed.project_id) == research_project_id]
    return seed


@pytest.fixture
def member_id(plan: SeedPlan, research_admin: ProjectMemberSeed) -> UserID:
    """The user the files put on another project than `research`."""
    [seed] = [seed for seed in _seeds(plan) if seed is not research_admin]
    return seed.user_id


@pytest.fixture
async def api_joined(
    db: ExtendedAsyncSAEngine, applied: None, research_admin: ProjectMemberSeed, member_id: UserID
) -> UserID:
    """`member` put on `research` the way the roster API joins a user."""
    repository = RbacRosterRepository(RosterOpsProvider(db))
    [joined] = await repository.join_members(research_admin.project_id, [member_id])
    return UserID(joined.id)


@pytest.fixture
async def personal_project(
    repository: SeedRepository,
    applied: None,
    plan: SeedPlan,
    research_project_id: str,
    member_id: UserID,
) -> ProjectSeed:
    """A personal project of `member`, written by the project kind."""
    [research] = [
        item
        for batch in plan.batches
        for item in batch.items()
        if isinstance(item, ProjectSeed) and str(item.id) == research_project_id
    ]
    personal = research.model_copy(
        update={
            "id": ProjectID(uuid.uuid4()),
            "name": "member-personal",
            "type": ProjectType.PERSONAL,
            "creator_id": member_id,
        }
    )
    [result] = await repository.partial_write([personal.write()], overwrite=False)
    assert result.error is None
    return personal


@pytest.fixture
def personal_project_id(personal_project: ProjectSeed) -> ProjectID:
    return personal_project.id


def _seeds(plan: SeedPlan) -> list[ProjectMemberSeed]:
    return [
        item
        for batch in plan.batches
        for item in batch.items()
        if isinstance(item, ProjectMemberSeed)
    ]


def _node(entity_type: EntityType, entity_id: uuid.UUID) -> sa.ScalarSelect[Any]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(VirtualEntityRow.entity_type == entity_type, VirtualEntityRow.entity_id == entity_id)
        .scalar_subquery()
    )


async def _place(db: ExtendedAsyncSAEngine, project_id: ProjectID, user_id: UserID) -> _Place:
    async with db.begin_readonly() as conn:
        caps = await conn.execute(
            sa.select(EntityMembershipCapRow.permission, EntityMembershipCapRow.all_fields)
            .join(
                EntityMembershipRow, EntityMembershipRow.id == EntityMembershipCapRow.membership_id
            )
            .where(
                EntityMembershipRow.virtual_entity_id == _node(ProjectEntityType(), project_id),
                EntityMembershipRow.member_entity_id == _node(UserEntityType(), user_id),
            )
        )
        roles = await conn.scalars(
            sa.select(UserRoleRow.role_id)
            .join(RoleRow, RoleRow.id == UserRoleRow.role_id)
            .where(
                UserRoleRow.user_id == user_id,
                RoleRow.scope_type == ProjectEntityType(),
                RoleRow.scope_id == project_id,
            )
        )
        return {(str(row.permission), row.all_fields) for row in caps}, set(roles.all())


class TestApply:
    async def test_the_members_join_their_projects(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.PROJECT_MEMBER].succeeded == [seed.key() for seed in _seeds(plan)]
        assert results[SeedKind.PROJECT_MEMBER].failed == []
        for seed in _seeds(plan):
            caps, _ = await _place(db, seed.project_id, seed.user_id)
            assert caps

    async def test_a_seeded_member_has_the_rows_of_one_joined_through_the_api(
        self,
        db: ExtendedAsyncSAEngine,
        research_admin: ProjectMemberSeed,
        research_member_role_id: str,
        api_joined: UserID,
    ) -> None:
        joined = await _place(db, research_admin.project_id, api_joined)
        assert joined[1] == {uuid.UUID(research_member_role_id)}
        assert await _place(db, research_admin.project_id, research_admin.user_id) == joined

    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_applying_again_skips_and_leaves_the_rows(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        applied: None,
        overwrite: bool,
    ) -> None:
        places = [await _place(db, seed.project_id, seed.user_id) for seed in _seeds(plan)]

        results = await SeedApplier(repository).apply(plan, overwrite=overwrite)

        assert results[SeedKind.PROJECT_MEMBER].succeeded == []
        assert len(results[SeedKind.PROJECT_MEMBER].skipped) == len(_seeds(plan))
        assert [await _place(db, seed.project_id, seed.user_id) for seed in _seeds(plan)] == places

    @pytest.mark.parametrize(
        ("refused", "error"),
        [
            ("personal-project", PersonalProjectMemberAdditionError),
            ("missing-project", ProjectNotFound),
            ("missing-user", ProjectMemberNotJoinableError),
        ],
    )
    async def test_an_item_the_roster_refuses_fails_alone(
        self,
        repository: SeedRepository,
        research_admin: ProjectMemberSeed,
        member_id: UserID,
        personal_project_id: ProjectID,
        refused: str,
        error: type[Exception],
    ) -> None:
        updates: dict[str, dict[str, Any]] = {
            "personal-project": {"project_id": personal_project_id},
            "missing-project": {"project_id": ProjectID(uuid.uuid4())},
            "missing-user": {"user_id": UserID(uuid.uuid4())},
        }
        refused_item = research_admin.model_copy(update=updates[refused])
        joining = research_admin.model_copy(update={"user_id": member_id})

        results = await repository.partial_write(
            [refused_item.write(), joining.write()], overwrite=False
        )

        assert isinstance(results[0].error, error)
        assert results[1] == SeedWriteItemResult(written=True)

