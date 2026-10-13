"""`mgr seed apply` writes the categories through the prometheus query preset category
upserter."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_CONTAINER = "0198a5a0-0000-7000-8000-00000000e001"
_VLLM = "0198a5a0-0000-7000-8000-00000000e002"


@pytest.fixture
def plan(prometheus_query_preset_category_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([
        prometheus_query_preset_category_seed_dir
    ])


async def _categories(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, str | None]]:
    """Each category id with its name and description."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                PrometheusQueryPresetCategoryRow.id,
                PrometheusQueryPresetCategoryRow.name,
                PrometheusQueryPresetCategoryRow.description,
            )
        )
        return {str(row.id): (row.name, row.description) for row in rows}


async def _public_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The categories the public node holds as members."""
    public_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == GlobalEntityType(),
            VirtualEntityRow.entity_id == global_entity_id(GlobalEntityName.PUBLIC),
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == public_node,
                VirtualEntityRow.entity_type == "prometheus_query_preset_category",
            )
        )
        return {str(row.entity_id) for row in rows}


async def _update(db: ExtendedAsyncSAEngine, category_id: str, **values: str | None) -> None:
    async with db.begin_session() as sess:
        await sess.execute(
            sa.update(PrometheusQueryPresetCategoryRow)
            .where(PrometheusQueryPresetCategoryRow.id == uuid.UUID(category_id))
            .values(**values)
        )


class TestApply:
    async def test_an_empty_database_gets_every_category(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.PROMETHEUS_QUERY_PRESET_CATEGORY].succeeded == [_CONTAINER, _VLLM]
        assert await _categories(db) == {
            _CONTAINER: ("container", "Container-level utilization metrics"),
            _VLLM: ("vllm-inference", None),
        }

    async def test_a_created_category_is_created_in_public(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _public_members(db) == {_CONTAINER, _VLLM}

    async def test_an_existing_category_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        await _update(db, _CONTAINER, name="renamed", description=None)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        result = results[SeedKind.PROMETHEUS_QUERY_PRESET_CATEGORY]
        assert result.succeeded == []
        assert [failure.reason for failure in result.skipped] == ["exists", "exists"]
        assert (await _categories(db))[_CONTAINER] == ("renamed", None)

    async def test_overwrite_restores_the_seed_values(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        await _update(db, _CONTAINER, name="renamed", description=None)
        await _update(db, _VLLM, description="added through the API")

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.PROMETHEUS_QUERY_PRESET_CATEGORY].succeeded == [_CONTAINER, _VLLM]
        assert await _categories(db) == {
            _CONTAINER: ("container", "Container-level utilization metrics"),
            _VLLM: ("vllm-inference", None),
        }

    async def test_a_name_taken_by_another_row_skips_only_that_item(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        async with db.begin_session() as sess:
            await sess.execute(sa.insert(PrometheusQueryPresetCategoryRow).values(name="container"))

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        result = results[SeedKind.PROMETHEUS_QUERY_PRESET_CATEGORY]
        assert result.succeeded == [_VLLM]
        assert [failure.key for failure in result.skipped] == [_CONTAINER]
        assert result.skipped[0].reason.startswith("collides with a row")
        assert _CONTAINER not in await _categories(db)
