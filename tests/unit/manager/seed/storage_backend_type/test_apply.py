"""`mgr seed apply` writes the backend types through the storage backend type upserter."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.storage.types import (
    StorageBackendCapabilities,
    StorageBackendCapability,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.storage_backend.row import StorageBackendTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind


@pytest.fixture
def plan(storage_backend_type_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([storage_backend_type_seed_dir])


async def _types(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, frozenset[str]]]:
    """Each backend name with its row id and capabilities."""
    async with db.begin_readonly_session() as sess:
        rows = (await sess.scalars(sa.select(StorageBackendTypeRow))).all()
        return {row.name: (str(row.id), row.capabilities.supported) for row in rows}


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The backend types the global node holds as members."""
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
                VirtualEntityRow.entity_type == "storage_backend_type",
            )
        )
        return {str(row.entity_id) for row in rows}


async def _insert_vfs(db: ExtendedAsyncSAEngine, *capabilities: StorageBackendCapability) -> str:
    async with db.begin_session() as sess:
        row = StorageBackendTypeRow(
            name="vfs", capabilities=StorageBackendCapabilities(supported=frozenset(capabilities))
        )
        sess.add(row)
        await sess.flush()
        return str(row.id)


class TestApply:
    async def test_an_empty_database_gets_every_type(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.STORAGE_BACKEND_TYPE].succeeded == ["vfs", "noop"]
        types = await _types(db)
        assert {name: capabilities for name, (_, capabilities) in types.items()} == {
            "vfs": frozenset({
                StorageBackendCapability.VFOLDER,
                StorageBackendCapability.METRIC,
                StorageBackendCapability.FAST_FS_SIZE,
            }),
            "noop": frozenset(),
        }

    async def test_a_created_type_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == {row_id for row_id, _ in (await _types(db)).values()}

    async def test_an_existing_type_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        existing = await _insert_vfs(db, StorageBackendCapability.QUOTA)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.STORAGE_BACKEND_TYPE].succeeded == ["noop"]
        assert [failure.reason for failure in results[SeedKind.STORAGE_BACKEND_TYPE].skipped] == [
            "exists"
        ]
        assert (await _types(db))["vfs"] == (
            existing,
            frozenset({StorageBackendCapability.QUOTA}),
        )

    async def test_an_overwrite_replaces_the_capabilities_and_keeps_the_id(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        existing = await _insert_vfs(db, StorageBackendCapability.QUOTA)

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.STORAGE_BACKEND_TYPE].succeeded == ["vfs", "noop"]
        assert (await _types(db))["vfs"] == (
            existing,
            frozenset({
                StorageBackendCapability.VFOLDER,
                StorageBackendCapability.METRIC,
                StorageBackendCapability.FAST_FS_SIZE,
            }),
        )
        assert existing in await _global_members(db)
