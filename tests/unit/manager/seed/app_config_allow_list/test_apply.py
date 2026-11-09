"""`mgr seed apply` writes the allow-list entries through the app config allow-list
upserter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
import yaml

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind


@pytest.fixture
def plan(app_config_allow_list_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([app_config_allow_list_seed_dir])


def _plan_of(directory: Path, items: list[dict[str, Any]]) -> SeedPlan:
    """The definitions in ``directory`` plus an allow-list file stating ``items``."""
    (directory / "allow-list.yaml").write_text(
        yaml.safe_dump({"kind": "app_config_allow_list", "version": 1, "items": items})
    )
    return SeedPlanner(create_seed_kind_registry()).plan([directory])


async def _entries(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, int]]:
    """Each entry key with its row id and rank."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(AppConfigAllowListRow.__table__))
        return {f"{row.config_name}:{row.scope_type}": (str(row.id), row.rank) for row in rows}


async def _ranks(db: ExtendedAsyncSAEngine) -> dict[str, int]:
    return {key: rank for key, (_, rank) in (await _entries(db)).items()}


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The entries the global node holds as members."""
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
                VirtualEntityRow.entity_type == "app_config_allow_list",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_every_entry(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        """A rank left out takes the scope type's default."""
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.APP_CONFIG_ALLOW_LIST].succeeded == [
            "webui:public",
            "webui:user",
            "session_launcher:domain",
        ]
        assert await _ranks(db) == {
            "webui:public": 100,
            "webui:user": 350,
            "session_launcher:domain": 200,
        }

    async def test_a_created_entry_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == {id_ for id_, _ in (await _entries(db)).values()}

    async def test_an_existing_entry_is_skipped_and_kept(
        self,
        app_config_allow_list_seed_dir: Path,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        changed = _plan_of(
            app_config_allow_list_seed_dir,
            [{"config_name": "webui", "scope_type": "public", "rank": 150}],
        )

        results = await SeedApplier(repository).apply(changed, overwrite=False)

        assert results[SeedKind.APP_CONFIG_ALLOW_LIST].succeeded == []
        assert [skip.reason for skip in results[SeedKind.APP_CONFIG_ALLOW_LIST].skipped] == [
            "exists"
        ]
        assert (await _ranks(db))["webui:public"] == 100

    async def test_an_overwrite_updates_the_rank(
        self,
        app_config_allow_list_seed_dir: Path,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        before = await _entries(db)
        changed = _plan_of(
            app_config_allow_list_seed_dir,
            [
                {"config_name": "webui", "scope_type": "public", "rank": 150},
                {"config_name": "webui", "scope_type": "user"},
            ],
        )

        results = await SeedApplier(repository).apply(changed, overwrite=True)

        assert results[SeedKind.APP_CONFIG_ALLOW_LIST].succeeded == ["webui:public", "webui:user"]
        after = await _entries(db)
        assert after["webui:public"] == (before["webui:public"][0], 150)
        assert after["webui:user"] == (before["webui:user"][0], 300)

    async def test_an_entry_created_through_the_api_is_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        """A row the seed did not write keeps its id under an overwrite."""
        async with db.begin_session() as sess:
            await sess.execute(sa.insert(AppConfigDefinitionRow).values(config_name="webui"))
            await sess.execute(
                sa.insert(AppConfigAllowListRow).values(
                    config_name="webui", scope_type=AppConfigScopeType.PUBLIC, rank=1
                )
            )
        [existing] = (await _entries(db)).values()

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert "webui:public" in results[SeedKind.APP_CONFIG_ALLOW_LIST].succeeded
        assert (await _entries(db))["webui:public"] == (existing[0], 100)
        assert existing[0] in await _global_members(db)

    async def test_an_unregistered_config_name_fails_that_item_only(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        app_config_definition_seed_dir: Path,
    ) -> None:
        """The foreign key to the definitions refuses the item; the other item is written."""
        changed = _plan_of(
            app_config_definition_seed_dir,
            [
                {"config_name": "unregistered", "scope_type": "public"},
                {"config_name": "webui", "scope_type": "public"},
            ],
        )

        results = await SeedApplier(repository).apply(changed, overwrite=False)

        result = results[SeedKind.APP_CONFIG_ALLOW_LIST]
        assert result.succeeded == ["webui:public"]
        [failed] = result.failed
        assert failed.key == "unregistered:public"
        assert failed.reason.startswith("refers to a missing row")
        assert set(await _entries(db)) == {"webui:public"}
