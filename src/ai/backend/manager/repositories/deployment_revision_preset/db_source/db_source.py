"""Database source for deployment revision preset repository operations."""

from __future__ import annotations

import logging
from uuid import UUID

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.errors.resource import DeploymentRevisionPresetNotFound
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

RANK_GAP = 100


class DeploymentRevisionPresetDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_next_rank(self, variant_id: UUID) -> int:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(sa.func.max(DeploymentRevisionPresetRow.rank)).where(
                DeploymentRevisionPresetRow.runtime_variant == variant_id
            )
            max_rank = (await session.execute(stmt)).scalar_one_or_none()
            return (max_rank + RANK_GAP) if max_rank is not None else RANK_GAP

    async def create(
        self, creator: Creator[DeploymentRevisionPresetRow]
    ) -> DeploymentRevisionPresetData:
        async with self._db.begin_session() as session:
            result = await execute_creator(session, creator)
            return result.row.to_data()

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
        self, updater: Updater[DeploymentRevisionPresetRow]
    ) -> DeploymentRevisionPresetData:
        async with self._db.begin_session() as session:
            result = await execute_updater(session, updater)
            if result is None:
                raise DeploymentRevisionPresetNotFound(
                    f"Deployment revision preset with ID {updater.pk_value} not found."
                )
            return result.row.to_data()

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
