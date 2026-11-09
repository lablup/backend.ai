"""`mgr seed apply` writes the slot types through the resource slot type upserter."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
import yaml

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_CPU = "eff6619c-a85c-40f4-ae59-608b0f683b4f"
_MEM = "9d1a589e-2a78-491e-97d0-32d2a0079564"


@pytest.fixture
def plan(resource_slot_type_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([resource_slot_type_seed_dir])


async def _slot_types(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, str, int]]:
    """Each uuid with its slot name, display name and rank."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                ResourceSlotTypeRow.uuid,
                ResourceSlotTypeRow.slot_name,
                ResourceSlotTypeRow.display_name,
                ResourceSlotTypeRow.rank,
            )
        )
        return {str(row.uuid): (row.slot_name, row.display_name, row.rank) for row in rows}


async def _members_of(db: ExtendedAsyncSAEngine, scope: GlobalEntityName) -> set[str]:
    """The slot types the scope's node holds as members."""
    scope_node = (
        sa.select(VirtualEntityRow.id)
        .where(VirtualEntityRow.entity_id == global_entity_id(scope))
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == scope_node,
                VirtualEntityRow.entity_type == "resource_slot_type",
            )
        )
        return {str(row.entity_id) for row in rows}


def _rewrite(directory: Path, display_name: str, slot_name: str) -> None:
    """Restate the cpu item with another display name and slot name."""
    path = directory / "slots.yaml"
    document = yaml.safe_load(path.read_text())
    document["items"][0] |= {"display_name": display_name, "slot_name": slot_name}
    path.write_text(yaml.safe_dump(document))


class TestApply:
    async def test_an_empty_database_gets_every_slot_type(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.RESOURCE_SLOT_TYPE].succeeded == [_CPU, _MEM]
        assert await _slot_types(db) == {_CPU: ("cpu", "CPU", 100), _MEM: ("mem", "RAM", 200)}

    @pytest.mark.parametrize("scope", [GlobalEntityName.GLOBAL, GlobalEntityName.PUBLIC])
    async def test_a_created_slot_type_is_created_in_global_and_public(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        scope: GlobalEntityName,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _members_of(db, scope) == {_CPU, _MEM}

    async def test_an_existing_slot_type_is_skipped_and_kept(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        resource_slot_type_seed_dir: Path,
        plan: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        _rewrite(resource_slot_type_seed_dir, "Processor", "cpu")
        changed = SeedPlanner(create_seed_kind_registry()).plan([resource_slot_type_seed_dir])

        results = await SeedApplier(repository).apply(changed, overwrite=False)

        assert results[SeedKind.RESOURCE_SLOT_TYPE].succeeded == []
        assert [failure.reason for failure in results[SeedKind.RESOURCE_SLOT_TYPE].skipped] == [
            "exists",
            "exists",
        ]
        assert (await _slot_types(db))[_CPU] == ("cpu", "CPU", 100)

    async def test_an_overwrite_updates_the_values_and_keeps_the_slot_name(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        resource_slot_type_seed_dir: Path,
        plan: SeedPlan,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        _rewrite(resource_slot_type_seed_dir, "Processor", "vcpu")
        changed = SeedPlanner(create_seed_kind_registry()).plan([resource_slot_type_seed_dir])

        results = await SeedApplier(repository).apply(changed, overwrite=True)

        assert results[SeedKind.RESOURCE_SLOT_TYPE].succeeded == [_CPU, _MEM]
        assert (await _slot_types(db))[_CPU] == ("cpu", "Processor", 100)

    async def test_a_slot_name_held_by_another_uuid_skips_only_that_item(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(ResourceSlotTypeRow).values(
                    slot_name="cpu", slot_type="count", display_name="Existing"
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        result = results[SeedKind.RESOURCE_SLOT_TYPE]
        assert result.succeeded == [_MEM]
        assert [failure.key for failure in result.skipped] == [_CPU]
        assert result.skipped[0].reason.startswith("collides with a row")
        slot_types = await _slot_types(db)
        assert _CPU not in slot_types
        assert ("cpu", "Existing", 0) in slot_types.values()
