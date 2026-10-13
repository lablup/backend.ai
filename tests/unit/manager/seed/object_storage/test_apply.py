"""`mgr seed apply` writes the storages through the object storage upserter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_MINIO = "0198a5a0-0000-7000-8000-00000000b001"
_ARCHIVE = "0198a5a0-0000-7000-8000-00000000b002"


@pytest.fixture
def plan(object_storage_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([object_storage_seed_dir])


async def _storages(db: ExtendedAsyncSAEngine) -> dict[str, dict[str, Any]]:
    """Each row by its id."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(ObjectStorageRow.__table__))
        return {str(row.id): dict(row._mapping) for row in rows}


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The storages the global node holds as members."""
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
                VirtualEntityRow.entity_type == "object_storage",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_every_storage(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.OBJECT_STORAGE].succeeded == [_MINIO, _ARCHIVE]
        storages = await _storages(db)
        assert storages[_MINIO]["name"] == "minio"
        assert storages[_MINIO]["region"] == "us-east-1"
        assert storages[_ARCHIVE]["region"] is None

    async def test_a_created_storage_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == {_MINIO, _ARCHIVE}

    async def test_an_existing_storage_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(ObjectStorageRow)
                .where(ObjectStorageRow.id == _MINIO)
                .values(endpoint="http://changed:9000")
            )
        storages = await _storages(db)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.OBJECT_STORAGE].succeeded == []
        assert [failure.reason for failure in results[SeedKind.OBJECT_STORAGE].skipped] == [
            "exists",
            "exists",
        ]
        assert await _storages(db) == storages

    async def test_an_overwrite_rewrites_the_values_but_keeps_the_name(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(ObjectStorageRow)
                .where(ObjectStorageRow.id == _MINIO)
                .values(name="renamed", endpoint="http://changed:9000", region=None)
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.OBJECT_STORAGE].succeeded == [_MINIO, _ARCHIVE]
        storage = (await _storages(db))[_MINIO]
        assert storage["name"] == "renamed"
        assert storage["endpoint"] == "http://127.0.0.1:9000"
        assert storage["region"] == "us-east-1"

    async def test_a_name_held_by_another_row_skips_only_that_storage(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(ObjectStorageRow).values(
                    name="minio",
                    host="other",
                    access_key="a",
                    secret_key="s",
                    endpoint="http://other:9000",
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.OBJECT_STORAGE].succeeded == [_ARCHIVE]
        [skipped] = results[SeedKind.OBJECT_STORAGE].skipped
        assert skipped.key == _MINIO
        assert skipped.reason.startswith("collides with a row")
        assert _MINIO not in await _storages(db)
