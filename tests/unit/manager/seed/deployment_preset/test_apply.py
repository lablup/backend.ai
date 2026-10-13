"""`mgr seed apply` writes the deployment preset files through the deployment preset
upserter, with one slot row per stated slot."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.deployment_preset.seed import DeploymentPresetSeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind


@pytest.fixture
def plan(deployment_preset_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([deployment_preset_seed_dir])


def _seeds(plan: SeedPlan) -> list[DeploymentPresetSeed]:
    return [
        item
        for batch in plan.batches
        for item in batch.items()
        if isinstance(item, DeploymentPresetSeed)
    ]


def _stated(seed: DeploymentPresetSeed) -> tuple[Any, ...]:
    return (
        seed.name,
        seed.description,
        seed.cluster_size,
        seed.replica_count,
        seed.deployment_strategy,
        seed.environ,
    )


async def _presets(db: ExtendedAsyncSAEngine) -> dict[str, tuple[Any, ...]]:
    row = DeploymentRevisionPresetRow
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                row.id,
                row.name,
                row.description,
                row.cluster_size,
                row.replica_count,
                row.deployment_strategy,
                row.environ,
            )
        )
        return {str(r.id): tuple(r)[1:] for r in rows}


async def _ranks(db: ExtendedAsyncSAEngine) -> dict[str, int]:
    row = DeploymentRevisionPresetRow
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(row.id, row.rank))
        return {str(r.id): r.rank for r in rows}


async def _slots(db: ExtendedAsyncSAEngine, preset_id: str) -> dict[str, Decimal]:
    row = PresetResourceSlotRow
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(row.slot_name, row.quantity).where(row.preset_id == preset_id)
        )
        return {r.slot_name: r.quantity for r in rows}


async def _members_of(db: ExtendedAsyncSAEngine, name: GlobalEntityName) -> set[str]:
    """The deployment presets the global entity holds as members."""
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
                VirtualEntityRow.entity_type == "deployment_preset",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_the_stated_rows(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        vllm_small_preset_id: str,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert len(results[SeedKind.DEPLOYMENT_PRESET].succeeded) == 2
        assert results[SeedKind.DEPLOYMENT_PRESET].skipped == []
        assert await _presets(db) == {str(seed.id): _stated(seed) for seed in _seeds(plan)}
        assert await _slots(db, vllm_small_preset_id) == {
            "cpu": Decimal(2),
            "mem": Decimal(4294967296),
        }

    async def test_presets_of_one_variant_are_ranked_in_file_order(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        ranks = await _ranks(db)
        assert sorted(ranks.values()) == [100, 200]

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
        vllm_small_preset_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(DeploymentRevisionPresetRow)
                .where(DeploymentRevisionPresetRow.id == vllm_small_preset_id)
                .values(description="edited")
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.DEPLOYMENT_PRESET].succeeded == []
        assert all(
            failure.reason.startswith("exists")
            for failure in results[SeedKind.DEPLOYMENT_PRESET].skipped
        )
        assert (await _presets(db))[vllm_small_preset_id][1] == "edited"

    async def test_overwrite_restores_the_seed_values_and_keeps_the_rank(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        vllm_small_preset_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        presets = await _presets(db)
        slots = await _slots(db, vllm_small_preset_id)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(DeploymentRevisionPresetRow)
                .where(DeploymentRevisionPresetRow.id == vllm_small_preset_id)
                .values(name="renamed", description=None, replica_count=9, rank=7)
            )
            await sess.execute(
                sa.update(PresetResourceSlotRow)
                .where(PresetResourceSlotRow.preset_id == vllm_small_preset_id)
                .where(PresetResourceSlotRow.slot_name == "cpu")
                .values(quantity=Decimal(8))
            )
            await sess.execute(
                sa.delete(PresetResourceSlotRow).where(
                    PresetResourceSlotRow.preset_id == vllm_small_preset_id,
                    PresetResourceSlotRow.slot_name == "mem",
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert len(results[SeedKind.DEPLOYMENT_PRESET].succeeded) == 2
        assert await _presets(db) == presets
        assert await _slots(db, vllm_small_preset_id) == slots
        assert (await _ranks(db))[vllm_small_preset_id] == 7

    async def test_overwrite_drops_a_slot_the_file_leaves_out(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        minimal_preset_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(PresetResourceSlotRow).values(
                    preset_id=minimal_preset_id, slot_name="cpu", quantity=Decimal(1)
                )
            )

        await SeedApplier(repository).apply(plan, overwrite=True)

        assert await _slots(db, minimal_preset_id) == {}

    async def test_a_name_held_by_another_id_in_the_variant_is_skipped(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        vllm_small_preset_id: str,
    ) -> None:
        """A preset created through the API under its own id keeps the name."""
        [stated] = [seed for seed in _seeds(plan) if str(seed.id) == vllm_small_preset_id]
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(DeploymentRevisionPresetRow).values(
                    runtime_variant=stated.runtime_variant_id,
                    name=stated.name,
                    rank=1,
                    image_id=stated.image_id,
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert [failure.key for failure in results[SeedKind.DEPLOYMENT_PRESET].skipped] == [
            vllm_small_preset_id
        ]
        assert vllm_small_preset_id not in await _presets(db)

    async def test_a_slot_name_no_slot_type_holds_fails_only_that_preset(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        vllm_small_preset_id: str,
        minimal_preset_id: str,
    ) -> None:
        """The slot types are left unapplied, so no slot name the presets state is held."""
        planned = SeedPlan(
            batches=[
                batch for batch in plan.batches if batch.kind.name == SeedKind.DEPLOYMENT_PRESET
            ],
            rejections=plan.rejections,
        )

        results = await SeedApplier(repository).apply(planned, overwrite=False)

        assert [failure.key for failure in results[SeedKind.DEPLOYMENT_PRESET].failed] == [
            vllm_small_preset_id
        ]
        assert set(await _presets(db)) == {minimal_preset_id}
