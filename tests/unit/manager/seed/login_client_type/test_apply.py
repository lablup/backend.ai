"""`mgr seed apply` writes the login client types through their upserter."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_WEBUI = "0198a5a0-0000-7000-8000-00000000c001"
_CLI = "0198a5a0-0000-7000-8000-00000000c002"


@pytest.fixture
def plan(login_client_type_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([login_client_type_seed_dir])


async def _types(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, str | None]]:
    """Each id with its name and description."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                LoginClientTypeRow.id, LoginClientTypeRow.name, LoginClientTypeRow.description
            )
        )
        return {str(row.id): (row.name, row.description) for row in rows}


async def _public_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The login client types the public node holds as members."""
    public_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == GlobalEntityType(),
            VirtualEntityRow.entity_id == global_entity_id(GlobalEntityName.PUBLIC),
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == public_node,
                VirtualEntityRow.entity_type == "login_client_type",
            )
        )
        return {str(row.entity_id) for row in rows}


async def _insert(
    db: ExtendedAsyncSAEngine, type_id: str, name: str, description: str | None
) -> None:
    async with db.begin_session() as sess:
        await sess.execute(
            sa.insert(LoginClientTypeRow).values(id=type_id, name=name, description=description)
        )


class TestApply:
    async def test_an_empty_database_gets_every_type(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.LOGIN_CLIENT_TYPE].succeeded == [_WEBUI, _CLI]
        assert await _types(db) == {_WEBUI: ("webui", "Web UI"), _CLI: ("cli", None)}

    async def test_a_created_type_is_created_in_public(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _public_members(db) == {_WEBUI, _CLI}

    async def test_an_existing_type_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await _insert(db, _WEBUI, "browser", None)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.LOGIN_CLIENT_TYPE].succeeded == [_CLI]
        assert [failure.key for failure in results[SeedKind.LOGIN_CLIENT_TYPE].skipped] == [_WEBUI]
        assert (await _types(db))[_WEBUI] == ("browser", None)

    async def test_overwrite_restores_the_seed_values(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await _insert(db, _WEBUI, "browser", None)
        await _insert(db, _CLI, "terminal", "edited")

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.LOGIN_CLIENT_TYPE].succeeded == [_WEBUI, _CLI]
        assert await _types(db) == {_WEBUI: ("webui", "Web UI"), _CLI: ("cli", None)}
        assert await _public_members(db) == {_WEBUI, _CLI}

    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_a_name_held_by_another_row_fails_only_that_item(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        overwrite: bool,
    ) -> None:
        other = "0198a5a0-0000-7000-8000-00000000c0ff"
        await _insert(db, other, "webui", None)

        results = await SeedApplier(repository).apply(plan, overwrite=overwrite)

        result = results[SeedKind.LOGIN_CLIENT_TYPE]
        assert result.succeeded == [_CLI]
        assert [failure.key for failure in result.skipped] == [_WEBUI]
        assert result.skipped[0].reason.startswith("collides with a row")
        assert await _types(db) == {other: ("webui", None), _CLI: ("cli", None)}
