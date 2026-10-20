"""`mgr seed apply` writes the runtime variant preset files through the runtime variant
preset upserter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.runtime_variant_preset.seed import RuntimeVariantPresetSeed
from ai.backend.manager.seed.types import SeedKind


@pytest.fixture
def plan(runtime_variant_preset_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([runtime_variant_preset_seed_dir])


def _seeds(plan: SeedPlan) -> list[RuntimeVariantPresetSeed]:
    return [item for item in plan.batches[0].items() if isinstance(item, RuntimeVariantPresetSeed)]


def _stated(seed: RuntimeVariantPresetSeed) -> tuple[Any, ...]:
    return (
        str(seed.runtime_variant_id),
        seed.name,
        seed.description,
        seed.rank,
        seed.preset_target,
        seed.value_type,
        seed.default_value,
        seed.preset_key,
        seed.required,
        seed.added_version,
        seed.deprecated_version,
        seed.category,
        seed.display_name,
        seed.ui_option,
    )


async def _presets(db: ExtendedAsyncSAEngine) -> dict[str, tuple[Any, ...]]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(RuntimeVariantPresetRow.__table__))
        return {
            str(row.id): (
                str(row.runtime_variant),
                row.name,
                row.description,
                row.rank,
                row.preset_target,
                row.value_type,
                row.default_value,
                row.key,
                row.required,
                row.added_version,
                row.deprecated_version,
                row.category,
                row.display_name,
                row.ui_option,
            )
            for row in rows
        }


async def _members_of(db: ExtendedAsyncSAEngine, name: GlobalEntityName) -> set[str]:
    """The runtime variant presets the global entity holds as members."""
    scope_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == GlobalEntityType(),
            VirtualEntityRow.entity_id == global_entity_id(name),
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == scope_node,
                VirtualEntityRow.entity_type == "runtime_variant_preset",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_the_stated_rows(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert len(results[SeedKind.RUNTIME_VARIANT_PRESET].succeeded) == 2
        assert results[SeedKind.RUNTIME_VARIANT_PRESET].skipped == []
        assert await _presets(db) == {str(seed.id): _stated(seed) for seed in _seeds(plan)}

    @pytest.mark.parametrize("scope", [GlobalEntityName.GLOBAL, GlobalEntityName.PUBLIC])
    async def test_a_created_preset_is_created_in_global_and_public(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        scope: GlobalEntityName,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _members_of(db, scope) == {str(seed.id) for seed in _seeds(plan)}

    async def test_an_existing_preset_is_skipped_and_listed(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        max_model_len_preset_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(RuntimeVariantPresetRow)
                .where(RuntimeVariantPresetRow.id == max_model_len_preset_id)
                .values(description="edited")
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.RUNTIME_VARIANT_PRESET].succeeded == []
        assert all(
            failure.reason.startswith("exists")
            for failure in results[SeedKind.RUNTIME_VARIANT_PRESET].skipped
        )
        assert (await _presets(db))[max_model_len_preset_id][2] == "edited"

    async def test_overwrite_restores_the_seed_values(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        max_model_len_preset_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        presets = await _presets(db)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(RuntimeVariantPresetRow)
                .where(RuntimeVariantPresetRow.id == max_model_len_preset_id)
                .values(
                    name="renamed",
                    rank=1,
                    default_value=None,
                    required=False,
                    ui_option=None,
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert len(results[SeedKind.RUNTIME_VARIANT_PRESET].succeeded) == 2
        assert await _presets(db) == presets

    async def test_a_name_held_by_another_id_in_the_variant_is_skipped(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        max_model_len_preset_id: str,
    ) -> None:
        """A preset the migration inserted under its own id keeps the name."""
        [stated] = [seed for seed in _seeds(plan) if str(seed.id) == max_model_len_preset_id]
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(RuntimeVariantPresetRow).values(
                    runtime_variant=stated.runtime_variant_id,
                    name=stated.name,
                    rank=100,
                    preset_target="args",
                    value_type="int",
                    key="--max-model-len",
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert [failure.key for failure in results[SeedKind.RUNTIME_VARIANT_PRESET].skipped] == [
            max_model_len_preset_id
        ]
        assert len(results[SeedKind.RUNTIME_VARIANT_PRESET].succeeded) == 1
        assert max_model_len_preset_id not in await _presets(db)
