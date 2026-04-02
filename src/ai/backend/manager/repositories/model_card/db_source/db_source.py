"""Database source for model card repository operations."""

from __future__ import annotations

import logging
from uuid import UUID

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.errors.resource import ModelCardNotFound
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelCardDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create(self, creator: Creator[ModelCardRow]) -> ModelCardData:
        async with self._db.begin_session() as session:
            result = await execute_creator(session, creator)
            return result.row.to_data()

    async def get_by_id(self, card_id: UUID) -> ModelCardData:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ModelCardRow).where(ModelCardRow.id == card_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise ModelCardNotFound()
            return row.to_data()

    async def update(self, updater: Updater[ModelCardRow]) -> ModelCardData:
        async with self._db.begin_session() as session:
            result = await execute_updater(session, updater)
            if result is None:
                raise ModelCardNotFound(f"Model card with ID {updater.pk_value} not found.")
            return result.row.to_data()

    async def delete(self, card_id: UUID) -> ModelCardData:
        async with self._db.begin_session() as session:
            stmt = sa.select(ModelCardRow).where(ModelCardRow.id == card_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise ModelCardNotFound()
            data = row.to_data()
            await session.delete(row)
        return data

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[ModelCardData], int, bool, bool]:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ModelCardRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.ModelCardRow.to_data() for row in result.rows]
            return items, result.total_count, result.has_next_page, result.has_previous_page
