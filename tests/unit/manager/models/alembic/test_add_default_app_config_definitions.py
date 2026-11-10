"""Runs the default app config revision against a real database and reads the rows
back."""

from __future__ import annotations

import importlib.util
import pathlib
import uuid
from collections.abc import AsyncGenerator
from typing import Final

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.alembic.versions import (
    ede445fb9d0d_add_the_default_app_config_definitions as revision,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    AppConfigDefinitionRow,
    AppConfigAllowListRow,
    AppConfigFragmentRow,
]

_DEFAULT_ENTRIES: Final[dict[str, int]] = {
    "userConfig:domain": 200,
    "userConfig:user": 300,
    "domainConfig:domain": 200,
    "publicConfigByDomain:public": 100,
}


@pytest.fixture
async def db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, _TABLES):
        yield global_entity_ids


@pytest.fixture
async def registered_by_admin(db: ExtendedAsyncSAEngine) -> dict[str, uuid.UUID]:
    """A `userConfig` definition and its `user` entry with a custom rank, written before
    the revision runs. Answers each row's id."""
    async with db.begin() as conn:
        definition_id = await conn.scalar(
            sa.insert(AppConfigDefinitionRow)
            .values(config_name="userConfig")
            .returning(AppConfigDefinitionRow.id)
        )
        entry_id = await conn.scalar(
            sa.insert(AppConfigAllowListRow)
            .values(config_name="userConfig", scope_type=AppConfigScopeType.USER, rank=350)
            .returning(AppConfigAllowListRow.id)
        )
    assert definition_id is not None and entry_id is not None
    return {"definition": definition_id, "entry": entry_id}


@pytest.fixture
async def fragment_on_a_default_entry(db: ExtendedAsyncSAEngine) -> None:
    """A public fragment on the `publicConfigByDomain` entry the revision wrote."""
    await _upgrade(db)
    async with db.begin() as conn:
        await conn.execute(
            sa.insert(AppConfigFragmentRow).values(
                config_name="publicConfigByDomain",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id=None,
                config={},
            )
        )


async def _upgrade(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(revision.add_defaults)


async def _downgrade(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(revision.remove_defaults)


async def _definitions(db: ExtendedAsyncSAEngine) -> dict[str, uuid.UUID]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(AppConfigDefinitionRow.config_name, AppConfigDefinitionRow.id)
        )
        return {row.config_name: row.id for row in rows}


async def _entries(db: ExtendedAsyncSAEngine) -> dict[str, tuple[uuid.UUID, int]]:
    """Each entry key with its row id and rank."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(AppConfigAllowListRow.__table__))
        return {f"{row.config_name}:{row.scope_type}": (row.id, row.rank) for row in rows}


async def _nodes(db: ExtendedAsyncSAEngine) -> set[tuple[str, uuid.UUID]]:
    """The app config definition and allow-list rows with a node."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_type, VirtualEntityRow.entity_id).where(
                VirtualEntityRow.entity_type.in_(["app_config_definition", "app_config_allow_list"])
            )
        )
        return {(str(row.entity_type), row.entity_id) for row in rows}


async def _global_members(db: ExtendedAsyncSAEngine) -> set[uuid.UUID]:
    """The entity ids `global` owns and governs, counted only where it does both."""
    global_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == "global",
            VirtualEntityRow.entity_id == global_entity_id(GlobalEntityName.GLOBAL),
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        owned = set(
            (
                await conn.scalars(
                    sa.select(VirtualEntityRow.entity_id)
                    .join(
                        EntityMembershipRow,
                        EntityMembershipRow.member_entity_id == VirtualEntityRow.id,
                    )
                    .where(EntityMembershipRow.virtual_entity_id == global_node)
                )
            ).all()
        )
        governed = set(
            (
                await conn.scalars(
                    sa.select(VirtualEntityRow.entity_id)
                    .join(ScopeBindingRow, ScopeBindingRow.virtual_entity_id == VirtualEntityRow.id)
                    .where(ScopeBindingRow.scope_entity_id == global_node)
                )
            ).all()
        )
    return owned & governed


class TestTheRevisionLoadsAsAlembicLoadsIt:
    async def test_the_module_executes_outside_sys_modules(self) -> None:
        path = pathlib.Path(revision.__file__)
        spec = importlib.util.spec_from_file_location(path.stem, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)

        assert module.revision == revision.revision
        assert module.down_revision == revision.down_revision


class TestAddDefaults:
    async def test_an_empty_database_gains_the_definitions_and_entries(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await _upgrade(db)

        assert set(await _definitions(db)) == {"userConfig", "domainConfig", "publicConfigByDomain"}
        ranks = {key: rank for key, (_, rank) in (await _entries(db)).items()}
        assert ranks == _DEFAULT_ENTRIES

    async def test_each_row_is_created_in_global(self, db: ExtendedAsyncSAEngine) -> None:
        await _upgrade(db)

        ids = {*(await _definitions(db)).values()} | {
            entry_id for entry_id, _ in (await _entries(db)).values()
        }
        assert {entity_id for _, entity_id in await _nodes(db)} == ids
        assert ids <= await _global_members(db)

    async def test_running_it_twice_leaves_the_same_rows(self, db: ExtendedAsyncSAEngine) -> None:
        await _upgrade(db)
        once = (await _definitions(db), await _entries(db), await _nodes(db))

        await _upgrade(db)

        assert (await _definitions(db), await _entries(db), await _nodes(db)) == once

    async def test_rows_registered_before_are_left_as_they_stand(
        self, db: ExtendedAsyncSAEngine, registered_by_admin: dict[str, uuid.UUID]
    ) -> None:
        await _upgrade(db)

        assert (await _definitions(db))["userConfig"] == registered_by_admin["definition"]
        entries = await _entries(db)
        assert entries["userConfig:user"] == (registered_by_admin["entry"], 350)
        assert set(entries) == set(_DEFAULT_ENTRIES)


class TestRemoveDefaults:
    async def test_the_downgrade_takes_back_what_it_wrote(self, db: ExtendedAsyncSAEngine) -> None:
        await _upgrade(db)

        await _downgrade(db)

        assert await _definitions(db) == {}
        assert await _entries(db) == {}
        assert await _nodes(db) == set()

    async def test_rows_registered_before_stay(
        self, db: ExtendedAsyncSAEngine, registered_by_admin: dict[str, uuid.UUID]
    ) -> None:
        await _upgrade(db)

        await _downgrade(db)

        assert await _definitions(db) == {"userConfig": registered_by_admin["definition"]}
        assert await _entries(db) == {"userConfig:user": (registered_by_admin["entry"], 350)}

    async def test_an_entry_a_fragment_refers_to_stays_with_its_definition(
        self, db: ExtendedAsyncSAEngine, fragment_on_a_default_entry: None
    ) -> None:
        await _downgrade(db)

        assert set(await _definitions(db)) == {"publicConfigByDomain"}
        entries = await _entries(db)
        assert set(entries) == {"publicConfigByDomain:public"}
        kept = {
            (await _definitions(db))["publicConfigByDomain"],
            entries["publicConfigByDomain:public"][0],
        }
        assert {entity_id for _, entity_id in await _nodes(db)} == kept
