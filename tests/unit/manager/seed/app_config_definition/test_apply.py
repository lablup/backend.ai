"""`mgr seed apply` writes the definitions through the app config definition upserter."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind


@pytest.fixture
def plan(app_config_definition_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([app_config_definition_seed_dir])


async def _definitions(db: ExtendedAsyncSAEngine) -> dict[str, str]:
    """Each config name with its row id."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(AppConfigDefinitionRow.config_name, AppConfigDefinitionRow.id)
        )
        return {row.config_name: str(row.id) for row in rows}


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The definitions the global node holds as members."""
    global_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == GlobalEntityType(),
            VirtualEntityRow.entity_id == global_entity_id(GlobalEntityName.GLOBAL),
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == global_node,
                VirtualEntityRow.entity_type == "app_config_definition",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_every_definition(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.APP_CONFIG_DEFINITION].succeeded == ["webui", "session_launcher"]
        assert set(await _definitions(db)) == {"webui", "session_launcher"}

    async def test_a_created_definition_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == set((await _definitions(db)).values())

    async def test_an_existing_definition_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        definitions = await _definitions(db)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.APP_CONFIG_DEFINITION].succeeded == []
        assert [failure.reason for failure in results[SeedKind.APP_CONFIG_DEFINITION].skipped] == [
            "exists",
            "exists",
        ]
        assert await _definitions(db) == definitions

    async def test_a_definition_created_through_the_api_is_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        """A row the seed did not write keeps its id under an overwrite."""
        async with db.begin_session() as sess:
            await sess.execute(sa.insert(AppConfigDefinitionRow).values(config_name="webui"))
        existing = (await _definitions(db))["webui"]

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.APP_CONFIG_DEFINITION].succeeded == ["webui", "session_launcher"]
        assert (await _definitions(db))["webui"] == existing
        assert existing in await _global_members(db)
