"""`mgr seed apply` writes the storages through the VFS storage upserter."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
import yaml

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_LOCAL = "0198a5a0-0000-7000-8000-00000000b001"
_SHARED = "0198a5a0-0000-7000-8000-00000000b002"


@pytest.fixture
def plan(vfs_storage_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([vfs_storage_seed_dir])


def _plan_of(path: Path, items: list[dict[str, str]]) -> SeedPlan:
    path.write_text(yaml.safe_dump({"kind": "vfs_storage", "version": 1, "items": items}))
    return SeedPlanner(create_seed_kind_registry()).plan([path])


async def _storages(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, str, str]]:
    """Each storage id with its name, host and base path."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(VFSStorageRow.__table__))
        return {str(row.id): (row.name, row.host, row.base_path) for row in rows}


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
                VirtualEntityRow.entity_type == "vfs_storage",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_every_storage(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.VFS_STORAGE].succeeded == [_LOCAL, _SHARED]
        assert await _storages(db) == {
            _LOCAL: ("local", "local", "/var/lib/backend.ai/vfs"),
            _SHARED: ("shared", "nfs", "/mnt/vfs"),
        }

    async def test_a_created_storage_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == {_LOCAL, _SHARED}

    async def test_an_existing_storage_is_skipped_and_kept(
        self,
        tmp_path: Path,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        changed = _plan_of(
            tmp_path / "changed.yaml",
            [{"id": _LOCAL, "name": "renamed", "host": "other", "base_path": "/other"}],
        )

        results = await SeedApplier(repository).apply(changed, overwrite=False)

        assert results[SeedKind.VFS_STORAGE].succeeded == []
        assert [skip.reason for skip in results[SeedKind.VFS_STORAGE].skipped] == ["exists"]
        assert (await _storages(db))[_LOCAL] == ("local", "local", "/var/lib/backend.ai/vfs")

    async def test_an_overwrite_updates_the_host_and_base_path_and_keeps_the_name(
        self,
        tmp_path: Path,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        changed = _plan_of(
            tmp_path / "changed.yaml",
            [{"id": _LOCAL, "name": "renamed", "host": "other", "base_path": "/other"}],
        )

        results = await SeedApplier(repository).apply(changed, overwrite=True)

        assert results[SeedKind.VFS_STORAGE].succeeded == [_LOCAL]
        assert (await _storages(db))[_LOCAL] == ("local", "other", "/other")

    async def test_a_name_held_by_another_storage_skips_that_item_only(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        """The unique name refuses the item; the other item is written."""
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(VFSStorageRow).values(name="local", host="api", base_path="/api")
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.VFS_STORAGE].succeeded == [_SHARED]
        [skipped] = results[SeedKind.VFS_STORAGE].skipped
        assert skipped.key == _LOCAL
        assert skipped.reason.startswith("collides with a row")
        storages = await _storages(db)
        assert _LOCAL not in storages
        assert _SHARED in storages
