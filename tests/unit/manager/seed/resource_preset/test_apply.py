"""`mgr seed apply` writes the resource preset files through the resource preset upserter."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
import yaml

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.resource_preset.seed import ResourcePresetSeed
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_RESOURCE_GROUP_ID = "0198a5a0-0000-7000-8000-000000001101"
_BOUND_PRESET_ID = "0198a5a0-0000-7000-8000-000000001102"


@pytest.fixture
def plan(resource_preset_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([resource_preset_seed_dir])


@pytest.fixture
async def resource_group(db: ExtendedAsyncSAEngine) -> str:
    """A resource group in the graph, named `gpu`."""
    async with db.begin_session() as sess:
        await sess.execute(
            sa.insert(ResourceGroupRow).values(
                id=_RESOURCE_GROUP_ID, name="gpu", driver="static", scheduler="fifo"
            )
        )
        await sess.execute(
            sa.insert(VirtualEntityRow).values(
                entity_type=ResourceGroupEntityType(), entity_id=_RESOURCE_GROUP_ID
            )
        )
    return _RESOURCE_GROUP_ID


@pytest.fixture
def bound_plan(tmp_path: Path, resource_group: str) -> SeedPlan:
    directory = tmp_path / "bound"
    directory.mkdir()
    preset = {
        "id": _BOUND_PRESET_ID,
        "name": "gpu-small",
        "resource_slots": {"cpu": "2", "mem": "2147483648", "cuda.shares": "1"},
        "resource_group_id": resource_group,
    }
    (directory / "gpu-small.yaml").write_text(
        yaml.safe_dump({"kind": "resource_preset", "version": 1, "items": [preset]})
    )
    return SeedPlanner(create_seed_kind_registry()).plan([directory])


def _seeds(plan: SeedPlan) -> list[ResourcePresetSeed]:
    return [item for item in plan.batches[0].items() if isinstance(item, ResourcePresetSeed)]


def _stated(seed: ResourcePresetSeed) -> tuple[Any, ...]:
    upserter_values = seed.write().upserter.build_update_values()
    return (
        seed.name,
        ResourceSlot(seed.resource_slots),
        upserter_values["shared_memory"],
        None,
    )


async def _presets(db: ExtendedAsyncSAEngine) -> dict[str, tuple[Any, ...]]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                ResourcePresetRow.id,
                ResourcePresetRow.name,
                ResourcePresetRow.resource_slots,
                ResourcePresetRow.shared_memory,
                ResourcePresetRow.scaling_group_name,
            )
        )
        return {
            str(row.id): (row.name, row.resource_slots, row.shared_memory, row.scaling_group_name)
            for row in rows
        }


async def _members_of(db: ExtendedAsyncSAEngine, scope_type: EntityType, scope_id: Any) -> set[str]:
    """The resource presets the scope holds as members."""
    scope_node = (
        sa.select(VirtualEntityRow.id)
        .where(VirtualEntityRow.entity_type == scope_type, VirtualEntityRow.entity_id == scope_id)
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == scope_node,
                VirtualEntityRow.entity_type == "resource_preset",
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

        assert len(results[SeedKind.RESOURCE_PRESET].succeeded) == 2
        assert results[SeedKind.RESOURCE_PRESET].skipped == []
        assert await _presets(db) == {str(seed.id): _stated(seed) for seed in _seeds(plan)}

    @pytest.mark.parametrize("scope", [GlobalEntityName.GLOBAL, GlobalEntityName.PUBLIC])
    async def test_an_unbound_preset_is_created_in_global_and_public(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        scope: GlobalEntityName,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _members_of(db, GlobalEntityType(), global_entity_id(scope)) == {
            str(seed.id) for seed in _seeds(plan)
        }

    async def test_a_bound_preset_is_created_in_global_and_its_resource_group(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        bound_plan: SeedPlan,
        resource_group: str,
    ) -> None:
        results = await SeedApplier(repository).apply(bound_plan, overwrite=False)

        assert len(results[SeedKind.RESOURCE_PRESET].succeeded) == 1
        assert (await _presets(db))[_BOUND_PRESET_ID][3] == "gpu"
        global_id = global_entity_id(GlobalEntityName.GLOBAL)
        public_id = global_entity_id(GlobalEntityName.PUBLIC)
        assert await _members_of(db, GlobalEntityType(), global_id) == {_BOUND_PRESET_ID}
        assert await _members_of(db, ResourceGroupEntityType(), resource_group) == {
            _BOUND_PRESET_ID
        }
        assert await _members_of(db, GlobalEntityType(), public_id) == set()

    async def test_an_existing_preset_is_skipped_and_listed(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        small_preset_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(ResourcePresetRow)
                .where(ResourcePresetRow.id == small_preset_id)
                .values(shared_memory=None)
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.RESOURCE_PRESET].succeeded == []
        assert all(
            failure.reason.startswith("exists")
            for failure in results[SeedKind.RESOURCE_PRESET].skipped
        )
        assert (await _presets(db))[small_preset_id][2] is None

    async def test_overwrite_restores_the_seed_values(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        small_preset_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        presets = await _presets(db)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(ResourcePresetRow)
                .where(ResourcePresetRow.id == small_preset_id)
                .values(
                    name="renamed",
                    resource_slots=ResourceSlot({"cpu": Decimal(4)}),
                    shared_memory=None,
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert len(results[SeedKind.RESOURCE_PRESET].succeeded) == 2
        assert await _presets(db) == presets

    async def test_overwrite_leaves_the_resource_group_binding(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        bound_plan: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(bound_plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(ResourcePresetRow)
                .where(ResourcePresetRow.id == _BOUND_PRESET_ID)
                .values(scaling_group_name="other")
            )

        await SeedApplier(repository).apply(bound_plan, overwrite=True)

        assert (await _presets(db))[_BOUND_PRESET_ID][3] == "other"

    async def test_a_name_held_by_another_id_is_skipped(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        small_preset_id: str,
    ) -> None:
        """A preset the fixture inserted under its own id keeps the name."""
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(ResourcePresetRow).values(
                    name="small", resource_slots=ResourceSlot({"cpu": Decimal(1)})
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert [failure.key for failure in results[SeedKind.RESOURCE_PRESET].skipped] == [
            small_preset_id
        ]
        assert len(results[SeedKind.RESOURCE_PRESET].succeeded) == 1
        assert small_preset_id not in await _presets(db)
