"""`mgr seed apply` writes the namespaces through the storage namespace upserter."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
import yaml

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_ARTIFACTS = "0198a5a0-0000-7000-8000-00000000c001"
_ARCHIVE = "0198a5a0-0000-7000-8000-00000000c002"
_MINIO = "0198a5a0-0000-7000-8000-00000000b001"
_ARCHIVE_STORAGE = "0198a5a0-0000-7000-8000-00000000b002"


@pytest.fixture
def plan(storage_namespace_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([storage_namespace_seed_dir])


def _plan_of(path: Path, items: list[dict[str, str]]) -> SeedPlan:
    path.write_text(yaml.safe_dump({"kind": "storage_namespace", "version": 1, "items": items}))
    return SeedPlanner(create_seed_kind_registry()).plan([path])


async def _namespaces(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, str]]:
    """Each namespace id with its storage id and namespace."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(StorageNamespaceRow.__table__))
        return {str(row.id): (str(row.storage_id), row.namespace) for row in rows}


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The namespaces the global node holds as members."""
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
                VirtualEntityRow.entity_type == "storage_namespace",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_every_namespace(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.STORAGE_NAMESPACE].succeeded == [_ARTIFACTS, _ARCHIVE]
        assert await _namespaces(db) == {
            _ARTIFACTS: (_MINIO, "artifacts"),
            _ARCHIVE: (_ARCHIVE_STORAGE, "archive"),
        }

    async def test_a_created_namespace_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == {_ARTIFACTS, _ARCHIVE}

    @pytest.mark.parametrize("overwrite", [False, True], ids=["skip", "overwrite"])
    async def test_an_existing_namespace_is_kept(
        self,
        overwrite: bool,
        tmp_path: Path,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        """The reservoir config looks the namespace up by storage and name, so an
        overwrite keeps both."""
        await SeedApplier(repository).apply(plan, overwrite=False)
        changed = _plan_of(
            tmp_path / "changed.yaml",
            [{"id": _ARTIFACTS, "storage_id": _ARCHIVE_STORAGE, "namespace": "renamed"}],
        )

        results = await SeedApplier(repository).apply(changed, overwrite=overwrite)

        assert results[SeedKind.STORAGE_NAMESPACE].succeeded == []
        assert [skip.reason for skip in results[SeedKind.STORAGE_NAMESPACE].skipped] == ["exists"]
        assert (await _namespaces(db))[_ARTIFACTS] == (_MINIO, "artifacts")

    async def test_a_namespace_held_in_the_same_storage_skips_that_item_only(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        """The unique storage and namespace refuse the item; the other item is written."""
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(StorageNamespaceRow).values(storage_id=_MINIO, namespace="artifacts")
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.STORAGE_NAMESPACE].succeeded == [_ARCHIVE]
        [skipped] = results[SeedKind.STORAGE_NAMESPACE].skipped
        assert skipped.key == _ARTIFACTS
        assert skipped.reason.startswith("collides with a row")
        namespaces = await _namespaces(db)
        assert _ARTIFACTS not in namespaces
        assert _ARCHIVE in namespaces
