"""Database source for prometheus query preset repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.exception import PrometheusQueryPresetNotFound
from ai.backend.manager.data.prometheus_query_preset import (
    PrometheusQueryPresetData,
    PrometheusQueryPresetListResult,
)
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = ("PrometheusQueryPresetDBSource",)


class PrometheusQueryPresetDBSource:
    """Database source for prometheus query preset operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

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
        """Read presets for an internal caller.

        The API searches through the action. This stays for the metric repository,
        which resolves preset ids with no action to run.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(PrometheusQueryPresetRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.PrometheusQueryPresetRow.to_data() for row in result.rows]
            return PrometheusQueryPresetListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
