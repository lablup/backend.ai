"""Database source for runtime variant repository operations."""

from __future__ import annotations

import logging
from uuid import UUID

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.errors.resource import RuntimeVariantNotFound
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create(self, creator: Creator[RuntimeVariantRow]) -> RuntimeVariantData:
        async with self._db.begin_session() as session:
            result = await execute_creator(session, creator)
            return result.row.to_data()

    async def get_by_id(self, variant_id: UUID) -> RuntimeVariantData:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(RuntimeVariantRow).where(RuntimeVariantRow.id == variant_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise RuntimeVariantNotFound()
            return row.to_data()

    async def update(self, updater: Updater[RuntimeVariantRow]) -> RuntimeVariantData:
        async with self._db.begin_session() as session:
            result = await execute_updater(session, updater)
            if result is None:
                raise RuntimeVariantNotFound(
                    f"Runtime variant with ID {updater.pk_value} not found."
                )
            return result.row.to_data()

    async def delete(self, variant_id: UUID) -> RuntimeVariantData:
        async with self._db.begin_session() as session:
            stmt = sa.select(RuntimeVariantRow).where(RuntimeVariantRow.id == variant_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise RuntimeVariantNotFound()
            data = row.to_data()
            await session.delete(row)
        return data

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[RuntimeVariantData], int, bool, bool]:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(RuntimeVariantRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.RuntimeVariantRow.to_data() for row in result.rows]
            return items, result.total_count, result.has_next_page, result.has_previous_page
