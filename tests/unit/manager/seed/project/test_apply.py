"""`mgr seed apply` writes the project files through the project upserter."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.seed.provider import SeedOpsProvider
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.project.seed import ProjectSeed
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

# A graph edge with each end named by its entity, the project under test as "self".
type _Edge = tuple[str, str, str]
type _Project = tuple[str, str, ProjectType, str, str | None, bool, uuid.UUID | None]


@pytest.fixture
def plan(project_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([project_seed_dir])


@pytest.fixture
async def applied(repository: SeedRepository, plan: SeedPlan) -> None:
    """The project files applied, with the domain and the policies they refer to."""
    await SeedApplier(repository).apply(plan, overwrite=False)


@pytest.fixture
def research(plan: SeedPlan, research_project_id: str) -> ProjectSeed:
    [seed] = [seed for seed in _seeds(plan) if str(seed.id) == research_project_id]
    return seed


@pytest.fixture
async def creator_id(db: ExtendedAsyncSAEngine, applied: None, research: ProjectSeed) -> UserID:
    """A user of the projects' domain, created the way the user service creates one."""
    async with SeedOpsProvider(db).write_ops() as w:
        data = await w.create_role_managed_entity(
            UserCreator(
                email="creator@example.com",
                username="creator",
                password=PasswordInfo(
                    password="password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1_000,
                    salt_size=32,
                ),
                need_password_change=False,
                domain_id=research.domain_id,
                resource_policy="default",
            )
        )
    return UserID(data.id)


@pytest.fixture
async def runtime_project_id(
    db: ExtendedAsyncSAEngine, applied: None, research: ProjectSeed
) -> ProjectID:
    """A project created the way the project service creates one."""
    async with SeedOpsProvider(db).write_ops() as w:
        data = await w.create_role_managed_entity(
            ProjectCreator(
                name="runtime",
                domain_id=research.domain_id,
                domain_name="default",
                resource_policy="default",
            )
        )
        await w.restate_project_resource_policy_share(ProjectID(data.id))
    return ProjectID(data.id)


async def _projects(db: ExtendedAsyncSAEngine) -> dict[str, _Project]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                ProjectRow.id,
                ProjectRow.name,
                ProjectRow.domain_name,
                ProjectRow.type,
                ProjectRow.resource_policy,
                ProjectRow.description,
                ProjectRow.is_active,
                ProjectRow.creator_id,
            )
        )
        return {
            str(row.id): (
                row.name,
                row.domain_name,
                row.type,
                row.resource_policy,
                row.description,
                row.is_active,
                row.creator_id,
            )
            for row in rows
        }


async def _edges(db: ExtendedAsyncSAEngine, project_id: uuid.UUID) -> set[_Edge]:
    """The ownership and governance edges touching the project's node."""
    async with db.begin_readonly() as conn:
        nodes = {
            row.id: (str(row.entity_type), str(row.entity_id))
            for row in await conn.execute(
                sa.select(
                    VirtualEntityRow.id, VirtualEntityRow.entity_type, VirtualEntityRow.entity_id
                )
            )
        }
        memberships = (
            await conn.execute(
                sa.select(
                    EntityMembershipRow.virtual_entity_id, EntityMembershipRow.member_entity_id
                )
            )
        ).all()
        bindings = (
            await conn.execute(
                sa.select(ScopeBindingRow.virtual_entity_id, ScopeBindingRow.scope_entity_id)
            )
        ).all()
    project_node = (str(ProjectEntityType()), str(project_id))

    def name(node_id: uuid.UUID) -> str:
        node = nodes[node_id]
        return "self" if node == project_node else ":".join(node)

    edges: set[_Edge] = set()
    for relation, rows in (("owns", memberships), ("governs", bindings)):
        for owner, member in rows:
            if project_node in (nodes[owner], nodes[member]):
                edges.add((relation, name(owner), name(member)))
    return edges


def _seeds(plan: SeedPlan) -> list[ProjectSeed]:
    return [
        item for batch in plan.batches for item in batch.items() if isinstance(item, ProjectSeed)
    ]


class TestApply:
    async def test_an_empty_database_gets_the_seed_rows(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert len(results[SeedKind.PROJECT].succeeded) == len(_seeds(plan))
        assert results[SeedKind.PROJECT].failed == []
        assert await _projects(db) == {
            str(seed.id): (
                seed.name,
                "default",
                seed.type,
                "default",
                seed.description,
                seed.is_active,
                None,
            )
            for seed in _seeds(plan)
        }

    async def test_a_seeded_project_has_the_graph_edges_of_a_created_one(
        self,
        db: ExtendedAsyncSAEngine,
        research: ProjectSeed,
        runtime_project_id: ProjectID,
    ) -> None:
        created = await _edges(db, runtime_project_id)
        assert created
        assert await _edges(db, research.id) == created

    async def test_a_personal_project_records_its_creator(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        research: ProjectSeed,
        creator_id: UserID,
    ) -> None:
        personal = research.model_copy(
            update={
                "id": ProjectID(uuid.uuid4()),
                "name": "creator-personal",
                "type": ProjectType.PERSONAL,
                "creator_id": creator_id,
            }
        )

        [result] = await repository.partial_write([personal.write()], overwrite=False)

        assert result.error is None
        project = (await _projects(db))[str(personal.id)]
        assert (project[2], project[6]) == (ProjectType.PERSONAL, creator_id)

    async def test_an_existing_project_is_skipped_and_left_as_it_is(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        applied: None,
        research_project_id: str,
    ) -> None:
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(ProjectRow)
                .where(ProjectRow.id == research_project_id)
                .values(description="edited")
            )
        edges = await _edges(db, uuid.UUID(research_project_id))

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.PROJECT].succeeded == []
        assert len(results[SeedKind.PROJECT].skipped) == len(_seeds(plan))
        assert (await _projects(db))[research_project_id][4] == "edited"
        assert await _edges(db, uuid.UUID(research_project_id)) == edges

    async def test_overwrite_restores_the_seed_values_and_keeps_the_insert_only_ones(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        research: ProjectSeed,
    ) -> None:
        projects = await _projects(db)
        edges = await _edges(db, research.id)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(ProjectRow)
                .where(ProjectRow.id == research.id)
                .values(name="edited", description="edited", is_active=False)
            )
        retyped = research.model_copy(update={"type": ProjectType.MODEL_STORE})

        [result] = await repository.partial_write([retyped.write()], overwrite=True)

        assert result.written
        assert await _projects(db) == projects
        assert await _edges(db, research.id) == edges

    async def test_a_name_repeated_in_the_domain_fails_alone(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        research: ProjectSeed,
    ) -> None:
        repeated = research.model_copy(update={"id": ProjectID(uuid.uuid4())})
        fresh = research.model_copy(update={"id": ProjectID(uuid.uuid4()), "name": "fresh"})

        results = await repository.partial_write([repeated.write(), fresh.write()], overwrite=False)

        assert [result.error is None for result in results] == [False, True]
        projects = await _projects(db)
        assert str(repeated.id) not in projects
        assert str(fresh.id) in projects

    async def test_a_domain_that_is_not_there_fails_the_item(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        research: ProjectSeed,
    ) -> None:
        orphan = research.model_copy(
            update={"id": ProjectID(uuid.uuid4()), "domain_id": DomainID(uuid.uuid4())}
        )

        [result] = await repository.partial_write([orphan.write()], overwrite=False)

        assert result.error is not None
        assert str(orphan.id) not in await _projects(db)

    async def test_a_second_personal_project_of_one_creator_fails_alone(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        research: ProjectSeed,
        creator_id: UserID,
    ) -> None:
        first, second = (
            research.model_copy(
                update={
                    "id": ProjectID(uuid.uuid4()),
                    "name": name,
                    "type": ProjectType.PERSONAL,
                    "creator_id": creator_id,
                }
            )
            for name in ("personal-1", "personal-2")
        )

        results = await repository.partial_write([first.write(), second.write()], overwrite=False)

        assert [result.error is None for result in results] == [True, False]
        projects = await _projects(db)
        assert str(first.id) in projects
        assert str(second.id) not in projects
