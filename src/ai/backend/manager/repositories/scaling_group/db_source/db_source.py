"""Database source for scaling group repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa

from ai.backend.manager.data.scaling_group.types import ScalingGroupListResult
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base import Querier, execute_querier

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = (
    "ScalingGroupDBSource",
    "ScalingGroupListResult",
)


class ScalingGroupDBSource:
    """
    Database source for scaling group operations.
    Handles all database operations for scaling groups.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def search_scaling_groups(
        self,
        querier: Optional[Querier] = None,
    ) -> ScalingGroupListResult:
        """Searches scaling groups with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(
                ScalingGroupRow,
                sa.func.count().over().label("total_count"),
            )

            result = await execute_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.ScalingGroupRow.to_dataclass() for row in result.rows]

            return ScalingGroupListResult(
                items=items,
                total_count=result.total_count,
            )
