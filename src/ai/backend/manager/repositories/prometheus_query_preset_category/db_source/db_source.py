"""Database source for prometheus query preset category repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.common.exception import PrometheusQueryPresetCategoryNotFound
from ai.backend.manager.data.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryData,
    PrometheusQueryPresetCategoryListResult,
)
from ai.backend.manager.models.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    execute_batch_querier,
    execute_creator,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = ("PrometheusQueryPresetCategoryDBSource",)


class PrometheusQueryPresetCategoryDBSource:
    """Database source for prometheus query preset category operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create(
        self,
        creator: Creator[PrometheusQueryPresetCategoryRow],
    ) -> PrometheusQueryPresetCategoryData:
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    async def delete(self, category_id: UUID) -> bool:
        async with self._db.begin_session() as db_sess:
            stmt = sa.delete(PrometheusQueryPresetCategoryRow).where(
                PrometheusQueryPresetCategoryRow.id == category_id
            )
            result = await db_sess.execute(stmt)
            if cast(CursorResult[Any], result).rowcount == 0:
                raise PrometheusQueryPresetCategoryNotFound(
                    f"Prometheus query preset category {category_id} not found"
                )
            return True

    async def get_by_id(self, category_id: UUID) -> PrometheusQueryPresetCategoryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.get(PrometheusQueryPresetCategoryRow, category_id)
            if row is None:
                raise PrometheusQueryPresetCategoryNotFound(
                    f"Prometheus query preset category {category_id} not found"
                )
            return row.to_data()

    async def search(
        self,
        querier: BatchQuerier,
    ) -> PrometheusQueryPresetCategoryListResult:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(PrometheusQueryPresetCategoryRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.PrometheusQueryPresetCategoryRow.to_data() for row in result.rows]
            return PrometheusQueryPresetCategoryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
