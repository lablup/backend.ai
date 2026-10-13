"""`mgr seed apply` writes the session template files through the session template
upserter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
import yaml

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.session_template.row import SessionTemplateRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.session_template.seed import SessionTemplateSeed
from ai.backend.manager.seed.types import SeedKind

_PROJECT_ID = "0198a5a0-0000-7000-8000-000000001301"
_PROJECT_TEMPLATE_ID = "0198a5a0-0000-7000-8000-000000001302"
_UNKNOWN_USER_ID = "0198a5a0-0000-7000-8000-000000001303"
_ORPHAN_TEMPLATE_ID = "0198a5a0-0000-7000-8000-000000001304"


@pytest.fixture
def plan(session_template_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([session_template_seed_dir])


@pytest.fixture
async def project(db: ExtendedAsyncSAEngine) -> str:
    """A project in the graph, in the owner's domain."""
    async with db.begin_session() as sess:
        await sess.execute(
            sa.insert(ProjectResourcePolicyRow).values(
                name="templates",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
        )
        await sess.execute(
            sa.insert(ProjectRow).values(
                id=_PROJECT_ID,
                name="research",
                domain_name="templates",
                resource_policy="templates",
            )
        )
        await sess.execute(
            sa.insert(VirtualEntityRow).values(
                entity_type=ProjectEntityType(), entity_id=_PROJECT_ID
            )
        )
    return _PROJECT_ID


def _plan_of(directory: Path, templates: list[dict[str, Any]]) -> SeedPlan:
    directory.mkdir()
    (directory / "templates.yaml").write_text(
        yaml.safe_dump({"kind": "session_template", "version": 1, "items": templates})
    )
    return SeedPlanner(create_seed_kind_registry()).plan([directory])


@pytest.fixture
def project_plan(tmp_path: Path, template_owner: str, project: str) -> SeedPlan:
    template = {
        "id": _PROJECT_TEMPLATE_ID,
        "user_id": template_owner,
        "project_id": project,
        "template": {"spec": {}},
    }
    return _plan_of(tmp_path / "project", [template])


@pytest.fixture
def orphan_plan(tmp_path: Path, template_owner: str) -> SeedPlan:
    templates = [
        {"id": _ORPHAN_TEMPLATE_ID, "user_id": _UNKNOWN_USER_ID, "template": {}},
        {"id": _PROJECT_TEMPLATE_ID, "user_id": template_owner, "template": {}},
    ]
    return _plan_of(tmp_path / "orphan", templates)


def _seeds(plan: SeedPlan) -> list[SessionTemplateSeed]:
    return [item for item in plan.batches[0].items() if isinstance(item, SessionTemplateSeed)]


def _stated(seed: SessionTemplateSeed) -> tuple[Any, ...]:
    return (
        str(seed.user_id),
        "templates",
        None,
        seed.type,
        seed.name,
        seed.is_active,
        seed.template,
    )


async def _templates(db: ExtendedAsyncSAEngine) -> dict[str, tuple[Any, ...]]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                SessionTemplateRow.id,
                SessionTemplateRow.user_uuid,
                SessionTemplateRow.domain_name,
                SessionTemplateRow.group_id,
                SessionTemplateRow.type,
                SessionTemplateRow.name,
                SessionTemplateRow.is_active,
                SessionTemplateRow.template,
            )
        )
        return {
            str(row.id): (
                str(row.user_uuid),
                row.domain_name,
                str(row.group_id) if row.group_id is not None else None,
                row.type,
                row.name,
                row.is_active,
                row.template,
            )
            for row in rows
        }


async def _members_of(db: ExtendedAsyncSAEngine, scope_type: EntityType, scope_id: Any) -> set[str]:
    """The session templates the scope holds as members."""
    scope_node = (
        sa.select(VirtualEntityRow.id)
        .where(VirtualEntityRow.entity_type == scope_type, VirtualEntityRow.entity_id == scope_id)
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == scope_node,
                VirtualEntityRow.entity_type == "session_template",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_the_stated_rows_in_the_owner_domain(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert len(results[SeedKind.SESSION_TEMPLATE].succeeded) == 2
        assert results[SeedKind.SESSION_TEMPLATE].skipped == []
        assert await _templates(db) == {str(seed.id): _stated(seed) for seed in _seeds(plan)}

    async def test_a_template_is_created_in_its_owner(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        template_owner: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _members_of(db, UserEntityType(), template_owner) == {
            str(seed.id) for seed in _seeds(plan)
        }

    async def test_a_project_template_is_created_in_its_owner_and_its_project(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        project_plan: SeedPlan,
        template_owner: str,
        project: str,
    ) -> None:
        results = await SeedApplier(repository).apply(project_plan, overwrite=False)

        assert len(results[SeedKind.SESSION_TEMPLATE].succeeded) == 1
        assert (await _templates(db))[_PROJECT_TEMPLATE_ID][2] == project
        assert await _members_of(db, UserEntityType(), template_owner) == {_PROJECT_TEMPLATE_ID}
        assert await _members_of(db, ProjectEntityType(), project) == {_PROJECT_TEMPLATE_ID}

    async def test_an_existing_template_is_skipped_and_listed(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        task_template_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(SessionTemplateRow)
                .where(SessionTemplateRow.id == task_template_id)
                .values(is_active=False)
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.SESSION_TEMPLATE].succeeded == []
        assert all(
            failure.reason.startswith("exists")
            for failure in results[SeedKind.SESSION_TEMPLATE].skipped
        )
        assert (await _templates(db))[task_template_id][5] is False

    async def test_overwrite_restores_the_seed_values(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        task_template_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        templates = await _templates(db)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(SessionTemplateRow)
                .where(SessionTemplateRow.id == task_template_id)
                .values(name="renamed", is_active=False, template={"edited": True})
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert len(results[SeedKind.SESSION_TEMPLATE].succeeded) == 2
        assert await _templates(db) == templates

    async def test_overwrite_leaves_the_domain(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        task_template_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(sa.insert(DomainRow).values(name="other"))
            await sess.execute(
                sa.update(SessionTemplateRow)
                .where(SessionTemplateRow.id == task_template_id)
                .values(domain_name="other")
            )

        await SeedApplier(repository).apply(plan, overwrite=True)

        assert (await _templates(db))[task_template_id][1] == "other"

    async def test_an_owner_naming_no_user_fails_that_template_only(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        orphan_plan: SeedPlan,
    ) -> None:
        results = await SeedApplier(repository).apply(orphan_plan, overwrite=False)

        assert [
            failure.key
            for failure in (
                results[SeedKind.SESSION_TEMPLATE].skipped
                + results[SeedKind.SESSION_TEMPLATE].failed
            )
        ] == [_ORPHAN_TEMPLATE_ID]
        assert results[SeedKind.SESSION_TEMPLATE].succeeded == [_PROJECT_TEMPLATE_ID]
        assert set(await _templates(db)) == {_PROJECT_TEMPLATE_ID}
