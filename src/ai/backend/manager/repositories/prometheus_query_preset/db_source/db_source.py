"""Database source for prometheus query preset repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.common.exception import PrometheusQueryPresetNotFound
from ai.backend.manager.data.prometheus_query_preset import (
    PrometheusQueryPresetData,
    PrometheusQueryPresetListResult,
)
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    execute_batch_querier,
    execute_creator,
)
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = ("PrometheusQueryPresetDBSource",)


class PrometheusQueryPresetDBSource:
    """Database source for prometheus query preset operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create(
        self,
        creator: Creator[PrometheusQueryPresetRow],
    ) -> PrometheusQueryPresetData:
        """Creates a new prometheus query preset."""
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    async def update(
        self,
        updater: Updater[PrometheusQueryPresetRow],
    ) -> PrometheusQueryPresetData:
        """Updates an existing prometheus query preset."""
        async with self._db.begin_session() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise PrometheusQueryPresetNotFound(
                    f"Prometheus query preset {updater.pk_value} not found"
                )
            return result.row.to_data()

    async def delete(self, preset_id: UUID) -> bool:
        """Deletes a prometheus query preset."""
        async with self._db.begin_session() as db_sess:
            stmt = sa.delete(PrometheusQueryPresetRow).where(
                PrometheusQueryPresetRow.id == preset_id
            )
            result = await db_sess.execute(stmt)
            return cast(CursorResult[Any], result).rowcount > 0

    async def get_by_id(self, preset_id: UUID) -> PrometheusQueryPresetData:
        """Retrieves a prometheus query preset by ID."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.get(PrometheusQueryPresetRow, preset_id)
            if row is None:
                raise PrometheusQueryPresetNotFound(
                    f"Prometheus query preset {preset_id} not found"
                )
            return row.to_data()

    async def search(
        self,
        querier: BatchQuerier,
    ) -> PrometheusQueryPresetListResult:
        """Searches prometheus query presets with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(PrometheusQueryPresetRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.PrometheusQueryPresetRow.to_data() for row in result.rows]

            return PrometheusQueryPresetListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
