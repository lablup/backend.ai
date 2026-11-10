"""`mgr seed apply` writes the runtime variant files through the runtime variant upserter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.runtime_variant.seed import RuntimeVariantSeed
from ai.backend.manager.seed.types import SeedKind


@pytest.fixture
def plan(runtime_variant_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([runtime_variant_seed_dir])


def _seeds(plan: SeedPlan) -> list[RuntimeVariantSeed]:
    return [item for item in plan.batches[0].items() if isinstance(item, RuntimeVariantSeed)]


def _stated(seed: RuntimeVariantSeed) -> tuple[Any, ...]:
    return (
        seed.name,
        seed.description,
        seed.reads_vfolder_config_files,
        seed.default_model_definition.model_dump(exclude_unset=True),
    )


async def _variants(db: ExtendedAsyncSAEngine) -> dict[str, tuple[Any, ...]]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                RuntimeVariantRow.id,
                RuntimeVariantRow.name,
                RuntimeVariantRow.description,
                RuntimeVariantRow.reads_vfolder_config_files,
                RuntimeVariantRow.default_model_definition,
            )
        )
        return {
            str(row.id): (
                row.name,
                row.description,
                row.reads_vfolder_config_files,
                row.default_model_definition.model_dump(exclude_unset=True),
            )
            for row in rows
        }


async def _members_of(db: ExtendedAsyncSAEngine, name: GlobalEntityName) -> set[str]:
    """The runtime variants the global entity holds as members."""
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
                VirtualEntityRow.entity_type == "runtime_variant",
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

        assert len(results[SeedKind.RUNTIME_VARIANT].succeeded) == 2
        assert results[SeedKind.RUNTIME_VARIANT].skipped == []
        assert await _variants(db) == {str(seed.id): _stated(seed) for seed in _seeds(plan)}

    @pytest.mark.parametrize("scope", [GlobalEntityName.GLOBAL, GlobalEntityName.PUBLIC])
    async def test_a_created_variant_is_created_in_global_and_public(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        scope: GlobalEntityName,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _members_of(db, scope) == {str(seed.id) for seed in _seeds(plan)}

    async def test_an_existing_variant_is_skipped_and_listed(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        vllm_variant_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(RuntimeVariantRow)
                .where(RuntimeVariantRow.id == vllm_variant_id)
                .values(description="edited")
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.RUNTIME_VARIANT].succeeded == []
        assert all(
            failure.reason.startswith("exists")
            for failure in results[SeedKind.RUNTIME_VARIANT].skipped
        )
        assert (await _variants(db))[vllm_variant_id][1] == "edited"

    async def test_overwrite_restores_the_seed_values(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        vllm_variant_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        variants = await _variants(db)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(RuntimeVariantRow)
                .where(RuntimeVariantRow.id == vllm_variant_id)
                .values(name="renamed", description=None, reads_vfolder_config_files=False)
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert len(results[SeedKind.RUNTIME_VARIANT].succeeded) == 2
        assert await _variants(db) == variants

    async def test_a_name_held_by_another_id_is_skipped(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        vllm_variant_id: str,
    ) -> None:
        """A variant the migration inserted under its own id keeps the name."""
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(RuntimeVariantRow).values(
                    name="vllm",
                    description="vLLM",
                    default_model_definition=DefaultModelDefinition(),
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert [failure.key for failure in results[SeedKind.RUNTIME_VARIANT].skipped] == [
            vllm_variant_id
        ]
        assert vllm_variant_id not in await _variants(db)
