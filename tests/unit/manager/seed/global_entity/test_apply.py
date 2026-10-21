"""`mgr seed apply` writes the global entities a fresh database lacks, under their stated ids."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Iterator
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest
import sqlalchemy as sa
import yaml
from sqlalchemy import text

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.manager.data.permission.global_entity import GlobalEntityIDCache, global_entity_id
from ai.backend.manager.models.global_entity.row import GlobalEntityRow
from ai.backend.manager.models.global_entity.seed import SEED_GLOBAL_ENTITIES_SQL
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.global_entity.loader import GlobalEntityIDLoader
from ai.backend.manager.repositories.ops.v2.seed.provider import SeedOpsProvider
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind
from ai.backend.testutils.db import with_tables

_GLOBAL_ID = UUID("785a0db6-868b-40d2-bda9-ac6679d85b7e")
_PUBLIC_ID = UUID("0258d56a-4a34-4927-8eb8-615cb892618d")


@dataclass(frozen=True)
class _SingletonNode:
    holds_itself: bool
    governs_itself: bool


async def _global_entity_ids_by_name(db: ExtendedAsyncSAEngine) -> dict[str, UUID]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(GlobalEntityRow.name, GlobalEntityRow.id))
        return {str(row.name): row.id for row in rows}


async def _singleton_nodes_by_entity_id(db: ExtendedAsyncSAEngine) -> dict[UUID, _SingletonNode]:
    """Each global node by the entity it stands for, and whether it holds and governs itself."""
    async with db.begin_readonly() as conn:
        nodes = await conn.execute(
            sa.select(VirtualEntityRow.id, VirtualEntityRow.entity_id).where(
                VirtualEntityRow.entity_type == "global"
            )
        )
        memberships = {
            (row.virtual_entity_id, row.member_entity_id)
            for row in await conn.execute(
                sa.select(
                    EntityMembershipRow.virtual_entity_id, EntityMembershipRow.member_entity_id
                )
            )
        }
        bindings = {
            (row.virtual_entity_id, row.scope_entity_id)
            for row in await conn.execute(
                sa.select(ScopeBindingRow.virtual_entity_id, ScopeBindingRow.scope_entity_id)
            )
        }
        return {
            node.entity_id: _SingletonNode(
                holds_itself=(node.id, node.id) in memberships,
                governs_itself=(node.id, node.id) in bindings,
            )
            for node in nodes
        }


@pytest.fixture
async def db_without_global_entities(
    registered_models: None, database_connection: ExtendedAsyncSAEngine
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """A database built as `mgr schema oneshot` builds one: the tables, and no singleton."""
    async with with_tables(
        database_connection,
        [GlobalEntityRow, VirtualEntityRow, EntityMembershipRow, ScopeBindingRow],
    ):
        yield database_connection


@pytest.fixture
async def db_with_migrated_global_entities(
    db_without_global_entities: ExtendedAsyncSAEngine,
) -> ExtendedAsyncSAEngine:
    """The singletons as the migration writes them, under ids the database generates."""
    async with db_without_global_entities.begin() as conn:
        for statement in SEED_GLOBAL_ENTITIES_SQL:
            await conn.execute(text(statement))
    return db_without_global_entities


@pytest.fixture
def global_entity_plan(tmp_path: Path) -> SeedPlan:
    directory = tmp_path / "global_entity"
    directory.mkdir()
    (directory / "defaults.yaml").write_text(
        yaml.safe_dump({
            "kind": "global_entity",
            "version": 1,
            "items": [
                {"id": str(_GLOBAL_ID), "name": "global"},
                {"id": str(_PUBLIC_ID), "name": "public"},
            ],
        })
    )
    return SeedPlanner(create_seed_kind_registry()).plan([directory])


@pytest.fixture
def fresh_db_repository(db_without_global_entities: ExtendedAsyncSAEngine) -> SeedRepository:
    return SeedRepository(SeedOpsProvider(db_without_global_entities))


@pytest.fixture
def migrated_db_repository(
    db_with_migrated_global_entities: ExtendedAsyncSAEngine,
) -> SeedRepository:
    return SeedRepository(SeedOpsProvider(db_with_migrated_global_entities))


@pytest.fixture
async def global_entities_applied_once(
    fresh_db_repository: SeedRepository, global_entity_plan: SeedPlan
) -> None:
    await SeedApplier(fresh_db_repository).apply(global_entity_plan, overwrite=False)


@pytest.fixture
def global_entity_id_cache_cleared() -> Iterator[None]:
    try:
        yield
    finally:
        GlobalEntityIDCache.clear()


class TestApplyToAFreshDatabase:
    async def test_each_singleton_gets_its_stated_id(
        self,
        db_without_global_entities: ExtendedAsyncSAEngine,
        fresh_db_repository: SeedRepository,
        global_entity_plan: SeedPlan,
    ) -> None:
        results = await SeedApplier(fresh_db_repository).apply(global_entity_plan, overwrite=False)

        assert results[SeedKind.GLOBAL_ENTITY].succeeded == ["global", "public"]
        assert await _global_entity_ids_by_name(db_without_global_entities) == {
            "global": _GLOBAL_ID,
            "public": _PUBLIC_ID,
        }

    async def test_each_singleton_gets_a_node_holding_and_governing_itself(
        self, db_without_global_entities: ExtendedAsyncSAEngine, global_entities_applied_once: None
    ) -> None:
        assert await _singleton_nodes_by_entity_id(db_without_global_entities) == {
            _GLOBAL_ID: _SingletonNode(holds_itself=True, governs_itself=True),
            _PUBLIC_ID: _SingletonNode(holds_itself=True, governs_itself=True),
        }

    async def test_the_id_cache_loads_the_stated_ids_afterwards(
        self,
        db_without_global_entities: ExtendedAsyncSAEngine,
        global_entities_applied_once: None,
        global_entity_id_cache_cleared: None,
    ) -> None:
        await GlobalEntityIDLoader(db_without_global_entities).load()

        assert global_entity_id(GlobalEntityName.PUBLIC) == _PUBLIC_ID

    async def test_applying_again_changes_nothing(
        self,
        db_without_global_entities: ExtendedAsyncSAEngine,
        fresh_db_repository: SeedRepository,
        global_entity_plan: SeedPlan,
        global_entities_applied_once: None,
    ) -> None:
        again = await SeedApplier(fresh_db_repository).apply(global_entity_plan, overwrite=True)

        assert again[SeedKind.GLOBAL_ENTITY].succeeded == []
        assert await _global_entity_ids_by_name(db_without_global_entities) == {
            "global": _GLOBAL_ID,
            "public": _PUBLIC_ID,
        }


class TestApplyToAMigratedDatabase:
    async def test_the_singletons_the_migration_wrote_keep_their_ids(
        self,
        db_with_migrated_global_entities: ExtendedAsyncSAEngine,
        migrated_db_repository: SeedRepository,
        global_entity_plan: SeedPlan,
    ) -> None:
        migrated_ids = await _global_entity_ids_by_name(db_with_migrated_global_entities)

        results = await SeedApplier(migrated_db_repository).apply(
            global_entity_plan, overwrite=True
        )

        assert [skip.reason for skip in results[SeedKind.GLOBAL_ENTITY].skipped] == [
            "exists",
            "exists",
        ]
        assert await _global_entity_ids_by_name(db_with_migrated_global_entities) == migrated_ids
