"""`mgr seed apply` writes each fragment through the upserter of its scope."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
import yaml

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_DOMAIN_ID = "0198a5a0-0000-7000-8000-00000000d001"
_DOMAIN_KEY = f"session_launcher:domain:{_DOMAIN_ID}"


@pytest.fixture
def plan(app_config_fragment_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([app_config_fragment_seed_dir])


def _plan_of(directory: Path, items: list[dict[str, Any]]) -> SeedPlan:
    """The seeds in ``directory`` with the fragment file stating ``items`` instead."""
    (directory / "app_config_fragment" / "fragments.yaml").write_text(
        yaml.safe_dump({"kind": "app_config_fragment", "version": 1, "items": items})
    )
    return SeedPlanner(create_seed_kind_registry()).plan([directory])


async def _fragments(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, dict[str, Any]]]:
    """Each fragment key with its row id and config."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(AppConfigFragmentRow.__table__))
        return {
            ":".join(
                part
                for part in (row.config_name, row.scope_type, row.scope_id and str(row.scope_id))
                if part
            ): (str(row.id), row.config)
            for row in rows
        }


async def _configs(db: ExtendedAsyncSAEngine) -> dict[str, dict[str, Any]]:
    return {key: config for key, (_, config) in (await _fragments(db)).items()}


async def _members(db: ExtendedAsyncSAEngine, entity_type: str, entity_id: str) -> set[str]:
    """The fragments the node of ``entity_type`` and ``entity_id`` holds as members."""
    scope_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == entity_type,
            VirtualEntityRow.entity_id == entity_id,
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == scope_node,
                VirtualEntityRow.entity_type == "app_config_fragment",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_every_fragment(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.APP_CONFIG_FRAGMENT].succeeded == ["webui:public", _DOMAIN_KEY]
        assert await _configs(db) == {
            "webui:public": {"theme": "light"},
            _DOMAIN_KEY: {"default_image": "python:3.13"},
        }

    @pytest.mark.parametrize(
        "scope", [GlobalEntityName.GLOBAL, GlobalEntityName.PUBLIC], ids=lambda name: name.value
    )
    async def test_a_public_fragment_is_created_in_global_and_public(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        scope: GlobalEntityName,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        fragment_id, _ = (await _fragments(db))["webui:public"]
        members = await _members(db, str(GlobalEntityType()), str(global_entity_id(scope)))
        assert members == {fragment_id}

    async def test_a_domain_fragment_is_created_in_its_domain(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        fragment_id, _ = (await _fragments(db))[_DOMAIN_KEY]
        assert await _members(db, str(DomainEntityType()), _DOMAIN_ID) == {fragment_id}

    async def test_an_existing_fragment_is_skipped_and_kept(
        self,
        app_config_fragment_seed_dir: Path,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        changed = _plan_of(
            app_config_fragment_seed_dir,
            [{"config_name": "webui", "scope_type": "public", "config": {"theme": "dark"}}],
        )

        results = await SeedApplier(repository).apply(changed, overwrite=False)

        assert results[SeedKind.APP_CONFIG_FRAGMENT].succeeded == []
        assert [skip.reason for skip in results[SeedKind.APP_CONFIG_FRAGMENT].skipped] == ["exists"]
        assert (await _configs(db))["webui:public"] == {"theme": "light"}

    async def test_an_overwrite_replaces_the_config(
        self,
        app_config_fragment_seed_dir: Path,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        before = await _fragments(db)
        changed = _plan_of(
            app_config_fragment_seed_dir,
            [
                {"config_name": "webui", "scope_type": "public", "config": {"theme": "dark"}},
                {
                    "config_name": "session_launcher",
                    "scope_type": "domain",
                    "scope_id": _DOMAIN_ID,
                    "config": {},
                },
            ],
        )

        results = await SeedApplier(repository).apply(changed, overwrite=True)

        assert results[SeedKind.APP_CONFIG_FRAGMENT].succeeded == ["webui:public", _DOMAIN_KEY]
        after = await _fragments(db)
        assert after["webui:public"] == (before["webui:public"][0], {"theme": "dark"})
        assert after[_DOMAIN_KEY] == (before[_DOMAIN_KEY][0], {})

    async def test_a_fragment_written_through_the_api_is_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        """A row the seed did not write keeps its id under an overwrite."""
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(sa.delete(AppConfigFragmentRow))
            await sess.execute(
                sa.insert(AppConfigFragmentRow).values(
                    config_name="webui",
                    scope_type=AppConfigScopeType.PUBLIC,
                    scope_id=None,
                    config={"theme": "api"},
                )
            )
        [existing] = (await _fragments(db)).values()

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert "webui:public" in results[SeedKind.APP_CONFIG_FRAGMENT].succeeded
        assert (await _fragments(db))["webui:public"] == (existing[0], {"theme": "light"})
        assert existing[0] in await _members(
            db, str(GlobalEntityType()), str(global_entity_id(GlobalEntityName.PUBLIC))
        )

    async def test_a_scope_the_allow_list_does_not_admit_fails_that_item_only(
        self,
        app_config_fragment_seed_dir: Path,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
    ) -> None:
        """The foreign key to the allow list refuses the item; the other item is written."""
        changed = _plan_of(
            app_config_fragment_seed_dir,
            [
                {"config_name": "session_launcher", "scope_type": "public", "config": {}},
                {"config_name": "webui", "scope_type": "public", "config": {}},
            ],
        )

        results = await SeedApplier(repository).apply(changed, overwrite=False)

        result = results[SeedKind.APP_CONFIG_FRAGMENT]
        assert result.succeeded == ["webui:public"]
        [failed] = result.failed
        assert failed.key == "session_launcher:public"
        assert failed.reason.startswith("refers to a missing row")
        assert set(await _fragments(db)) == {"webui:public"}

    async def test_a_domain_that_does_not_exist_fails_that_item_only(
        self,
        app_config_fragment_seed_dir: Path,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
    ) -> None:
        """The domain has no virtual entity to own the fragment; the other item is written."""
        missing_domain_id = "0198a5a0-0000-7000-8000-00000000dfff"
        changed = _plan_of(
            app_config_fragment_seed_dir,
            [
                {
                    "config_name": "session_launcher",
                    "scope_type": "domain",
                    "scope_id": missing_domain_id,
                    "config": {},
                },
                {"config_name": "webui", "scope_type": "public", "config": {}},
            ],
        )

        results = await SeedApplier(repository).apply(changed, overwrite=False)

        result = results[SeedKind.APP_CONFIG_FRAGMENT]
        assert result.succeeded == ["webui:public"]
        [failed] = result.failed
        assert failed.key == f"session_launcher:domain:{missing_domain_id}"
        assert failed.reason.startswith("refers to a missing row")
        assert set(await _fragments(db)) == {"webui:public"}
