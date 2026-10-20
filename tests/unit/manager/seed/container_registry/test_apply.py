"""`mgr seed apply` writes the registries through the container registry upserter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_HARBOR = "0198a5a0-0000-7000-8000-00000000c001"
_LOCAL = "0198a5a0-0000-7000-8000-00000000c002"


@pytest.fixture
def plan(container_registry_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([container_registry_seed_dir])


async def _registries(db: ExtendedAsyncSAEngine) -> dict[str, dict[str, Any]]:
    """Each registry id with the columns the seed states."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(ContainerRegistryRow.__table__))
        return {str(row.id): dict(row._mapping) for row in rows}


async def _members(db: ExtendedAsyncSAEngine, scope: GlobalEntityName) -> set[str]:
    """The registries the scope's node holds as members."""
    scope_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == GlobalEntityType(),
            VirtualEntityRow.entity_id == global_entity_id(scope),
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == scope_node,
                VirtualEntityRow.entity_type == "container_registry",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_every_registry(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.CONTAINER_REGISTRY].succeeded == [_HARBOR, _LOCAL]
        registries = await _registries(db)
        assert registries[_HARBOR]["is_global"] is True
        assert registries[_HARBOR]["ssl_verify"] is True
        assert registries[_LOCAL]["is_global"] is False
        assert registries[_LOCAL]["password"] == "secret"
        assert registries[_LOCAL]["extra"] == {"note": "seed"}

    async def test_a_global_registry_is_created_in_public_as_well(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)

        assert await _members(db, GlobalEntityName.GLOBAL) == {_HARBOR, _LOCAL}
        assert await _members(db, GlobalEntityName.PUBLIC) == {_HARBOR}

    async def test_an_existing_registry_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(ContainerRegistryRow)
                .where(ContainerRegistryRow.id == _HARBOR)
                .values(url="https://changed.example.com")
            )
        registries = await _registries(db)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.CONTAINER_REGISTRY].succeeded == []
        assert [failure.reason for failure in results[SeedKind.CONTAINER_REGISTRY].skipped] == [
            "exists",
            "exists",
        ]
        assert await _registries(db) == registries

    async def test_an_overwrite_keeps_the_names_images_refer_to(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        """``url`` and the stated credentials are rewritten; ``registry_name``, ``project``,
        ``is_global`` and a credential the seed leaves null stay as the row had them."""
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(ContainerRegistryRow).values(
                    id=_HARBOR,
                    registry_name="renamed",
                    url="https://changed.example.com",
                    type=ContainerRegistryType.DOCKER,
                    project="community",
                    username="someone",
                    is_global=False,
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.CONTAINER_REGISTRY].succeeded == [_HARBOR, _LOCAL]
        registry = (await _registries(db))[_HARBOR]
        assert registry["url"] == "https://cr.backend.ai"
        assert registry["type"] == ContainerRegistryType.HARBOR2
        assert registry["username"] == "someone"
        assert (registry["registry_name"], registry["project"], registry["is_global"]) == (
            "renamed",
            "community",
            False,
        )
        assert _HARBOR in await _members(db, GlobalEntityName.GLOBAL)
        assert _HARBOR not in await _members(db, GlobalEntityName.PUBLIC)
