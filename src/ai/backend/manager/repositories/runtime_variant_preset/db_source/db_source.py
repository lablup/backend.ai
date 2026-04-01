"""Database source for runtime variant preset repository operations."""

from __future__ import annotations

import logging
from uuid import UUID

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.errors.resource import RuntimeVariantPresetNotFound
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

RANK_GAP = 100


class RuntimeVariantPresetDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_next_rank(self, variant_id: UUID) -> int:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(sa.func.max(RuntimeVariantPresetRow.rank)).where(
                RuntimeVariantPresetRow.runtime_variant == variant_id
            )
            max_rank = (await session.execute(stmt)).scalar_one_or_none()
            return (max_rank + RANK_GAP) if max_rank is not None else RANK_GAP

    async def create(self, creator: Creator[RuntimeVariantPresetRow]) -> RuntimeVariantPresetData:
        async with self._db.begin_session() as session:
            result = await execute_creator(session, creator)
            return result.row.to_data()

    async def get_by_id(self, preset_id: UUID) -> RuntimeVariantPresetData:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(RuntimeVariantPresetRow).where(RuntimeVariantPresetRow.id == preset_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise RuntimeVariantPresetNotFound()
            return row.to_data()

    async def update(self, updater: Updater[RuntimeVariantPresetRow]) -> RuntimeVariantPresetData:
        async with self._db.begin_session() as session:
            result = await execute_updater(session, updater)
            if result is None:
                raise RuntimeVariantPresetNotFound(
                    f"Runtime variant preset with ID {updater.pk_value} not found."
                )
            return result.row.to_data()

    async def delete(self, preset_id: UUID) -> RuntimeVariantPresetData:
        async with self._db.begin_session() as session:
            stmt = sa.select(RuntimeVariantPresetRow).where(RuntimeVariantPresetRow.id == preset_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise RuntimeVariantPresetNotFound()
            data = row.to_data()
            await session.delete(row)
        return data

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[RuntimeVariantPresetData], int, bool, bool]:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(RuntimeVariantPresetRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.RuntimeVariantPresetRow.to_data() for row in result.rows]
            return items, result.total_count, result.has_next_page, result.has_previous_page
