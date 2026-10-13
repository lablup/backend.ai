"""`mgr seed apply` writes the presets through the prometheus query preset upserter."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.prometheus_query_preset.row import (
    PresetOptions,
    PrometheusQueryPresetRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_SUM = "0198a5a0-0000-7000-8000-00000000f001"
_RATE = "0198a5a0-0000-7000-8000-00000000f002"
_CONTAINER = "0198a5a0-0000-7000-8000-00000000e001"
_MISSING_CATEGORY = "0198a5a0-0000-7000-8000-00000000e0ff"

_SEEDED: dict[str, tuple[Any, ...]] = {
    _SUM: (
        "container-utilization-sum",
        None,
        "Instant value of the per-kernel utilization, summed",
        100,
        _CONTAINER,
        PresetOptions(filter_labels=["kernel_id"], group_labels=["kernel_id"]),
    ),
    _RATE: (
        "vllm-request-rate",
        "5m",
        None,
        0,
        None,
        PresetOptions(filter_labels=[], group_labels=[]),
    ),
}


@pytest.fixture
def plan(prometheus_query_preset_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([prometheus_query_preset_seed_dir])


async def _presets(db: ExtendedAsyncSAEngine) -> dict[str, tuple[Any, ...]]:
    """Each preset id with its name, time window, description, rank, category and options."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                PrometheusQueryPresetRow.id,
                PrometheusQueryPresetRow.name,
                PrometheusQueryPresetRow.time_window,
                PrometheusQueryPresetRow.description,
                PrometheusQueryPresetRow.rank,
                PrometheusQueryPresetRow.category_id,
                PrometheusQueryPresetRow.options,
            )
        )
        return {
            str(row.id): (
                row.name,
                row.time_window,
                row.description,
                row.rank,
                str(row.category_id) if row.category_id is not None else None,
                row.options,
            )
            for row in rows
        }


async def _public_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The presets the public node holds as members."""
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
                VirtualEntityRow.entity_type == "prometheus_query_preset",
            )
        )
        return {str(row.entity_id) for row in rows}


async def _update(db: ExtendedAsyncSAEngine, preset_id: str, **values: Any) -> None:
    async with db.begin_session() as sess:
        await sess.execute(
            sa.update(PrometheusQueryPresetRow)
            .where(PrometheusQueryPresetRow.id == uuid.UUID(preset_id))
            .values(**values)
        )


class TestApply:
    async def test_an_empty_database_gets_every_preset(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.PROMETHEUS_QUERY_PRESET].succeeded == [_SUM, _RATE]
        assert await _presets(db) == _SEEDED

    async def test_a_created_preset_is_created_in_public(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _public_members(db) == {_SUM, _RATE}

    async def test_an_existing_preset_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        await _update(db, _SUM, name="renamed", rank=1, category_id=None)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        result = results[SeedKind.PROMETHEUS_QUERY_PRESET]
        assert result.succeeded == []
        assert [failure.reason for failure in result.skipped] == ["exists", "exists"]
        assert (await _presets(db))[_SUM][:5] == ("renamed", None, _SEEDED[_SUM][2], 1, None)

    async def test_overwrite_restores_the_seed_values(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        await _update(db, _SUM, name="renamed", rank=1, category_id=None)
        await _update(
            db,
            _RATE,
            time_window="1h",
            description="added through the API",
            options=PresetOptions(filter_labels=["agent_id"], group_labels=[]),
        )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.PROMETHEUS_QUERY_PRESET].succeeded == [_SUM, _RATE]
        assert await _presets(db) == _SEEDED

    async def test_a_missing_category_fails_only_that_item(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        prometheus_query_preset_seed_dir: Path,
    ) -> None:
        presets = prometheus_query_preset_seed_dir / "presets.yaml"
        presets.write_text(presets.read_text().replace(_CONTAINER, _MISSING_CATEGORY))
        plan = SeedPlanner(create_seed_kind_registry()).plan([prometheus_query_preset_seed_dir])

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        result = results[SeedKind.PROMETHEUS_QUERY_PRESET]
        assert result.succeeded == [_RATE]
        assert [failure.key for failure in result.failed] == [_SUM]
        assert result.failed[0].reason.startswith("refers to a missing row")
        assert set(await _presets(db)) == {_RATE}
