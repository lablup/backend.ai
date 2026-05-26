"""Database source for deployment revision preset repository operations."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.errors.resource import DeploymentRevisionPresetNotFound
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow, ResourceSlotTypeRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchPurger,
    BatchQuerier,
    NextValuePolicy,
    execute_batch_querier,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment_revision_preset.creators import (
    DeploymentRevisionPresetCreatorSpec,
    PresetResourceSlotDependentCreatorSpec,
    PresetSlotDependency,
)
from ai.backend.manager.repositories.deployment_revision_preset.purgers import (
    PresetResourceSlotBatchPurgerSpec,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

RANK_GAP = 100


class DeploymentRevisionPresetDBSource:
    _db: ExtendedAsyncSAEngine
    _ops: DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._ops = DBOpsProvider(db)

    async def create(
        self,
        spec: DeploymentRevisionPresetCreatorSpec,
        slot_specs: Sequence[PresetResourceSlotDependentCreatorSpec],
    ) -> DeploymentRevisionPresetData:
        policy = NextValuePolicy(
            column=DeploymentRevisionPresetRow.rank,
            scope_condition=lambda: DeploymentRevisionPresetRow.runtime_variant
            == spec.runtime_variant_id,
            lock_selector=sa.select(RuntimeVariantRow).where(
                RuntimeVariantRow.id == spec.runtime_variant_id
            ),
            gap=RANK_GAP,
        )
        async with self._ops.write_ops() as w:
            created = await w.create_with_next_value(policy, spec)
            preset = created.row
            await w.bulk_create_dependent(slot_specs, PresetSlotDependency(preset_id=preset.id))
            return preset.to_data()

    async def get_by_id(self, preset_id: UUID) -> DeploymentRevisionPresetData:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(DeploymentRevisionPresetRow).where(
                DeploymentRevisionPresetRow.id == preset_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise DeploymentRevisionPresetNotFound()
            return row.to_data()

    async def update(
        self,
        updater: Updater[DeploymentRevisionPresetRow],
        slot_specs: Sequence[PresetResourceSlotDependentCreatorSpec] | None,
    ) -> DeploymentRevisionPresetData:
        async with self._ops.write_ops() as w:
            result = await w.update(updater)
            if result is None:
                raise DeploymentRevisionPresetNotFound(
                    f"Deployment revision preset with ID {updater.pk_value} not found."
                )
            preset = result.row
            if slot_specs is not None:
                await w.batch_purge(
                    BatchPurger(spec=PresetResourceSlotBatchPurgerSpec(preset_id=preset.id))
                )
                await w.bulk_create_dependent(slot_specs, PresetSlotDependency(preset_id=preset.id))
            return preset.to_data()

    async def delete(self, preset_id: UUID) -> DeploymentRevisionPresetData:
        async with self._db.begin_session() as session:
            stmt = sa.select(DeploymentRevisionPresetRow).where(
                DeploymentRevisionPresetRow.id == preset_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise DeploymentRevisionPresetNotFound()
            data = row.to_data()
            await session.delete(row)
        return data

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[DeploymentRevisionPresetData], int, bool, bool]:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(DeploymentRevisionPresetRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.DeploymentRevisionPresetRow.to_data() for row in result.rows]
            return items, result.total_count, result.has_next_page, result.has_previous_page

    async def get_resource_slots(
        self,
        preset_id: UUID,
    ) -> list[tuple[str, Decimal]]:
        """Get all resource slots for a preset (no pagination)."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(PresetResourceSlotRow).where(
                PresetResourceSlotRow.preset_id == preset_id
            )
            rows = (await db_sess.execute(stmt)).scalars().all()
            return [(r.slot_name, r.quantity) for r in rows]

    async def search_resource_slots(
        self,
        preset_id: UUID,
        querier: BatchQuerier,
    ) -> tuple[list[tuple[str, Decimal]], int, bool, bool]:
        """Search resource slots allocated to a preset.

        Returns (items, total_count, has_next_page, has_previous_page).
        Each item is a (slot_name, quantity) tuple.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(PresetResourceSlotRow, ResourceSlotTypeRow.rank)
                .join(
                    ResourceSlotTypeRow,
                    PresetResourceSlotRow.slot_name == ResourceSlotTypeRow.slot_name,
                )
                .where(PresetResourceSlotRow.preset_id == preset_id)
            )
            result = await execute_batch_querier(db_sess, query, querier)
            items: list[tuple[str, Decimal]] = [
                (row.PresetResourceSlotRow.slot_name, row.PresetResourceSlotRow.quantity)
                for row in result.rows
            ]
            return items, result.total_count, result.has_next_page, result.has_previous_page
