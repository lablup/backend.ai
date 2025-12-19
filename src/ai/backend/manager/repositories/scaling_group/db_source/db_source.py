"""Database source for scaling group repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import sqlalchemy as sa

from ai.backend.common.exception import ScalingGroupConflict
from ai.backend.manager.data.scaling_group.types import ScalingGroupData, ScalingGroupListResult
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.scaling_group.creators import ScalingGroupCreatorSpec

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

    async def create_scaling_group(
        self,
        creator: Creator[ScalingGroupRow],
    ) -> ScalingGroupData:
        """Creates a new scaling group.

        Raises ScalingGroupConflict if a scaling group with the same name already exists.
        """
        async with self._db.begin_session() as session:
            try:
                result = await execute_creator(session, creator)
            except sa.exc.IntegrityError:
                spec = cast(ScalingGroupCreatorSpec, creator.spec)
                raise ScalingGroupConflict(f"Duplicate scaling group name: {spec.name}")
            return result.row.to_dataclass()

    async def search_scaling_groups(
        self,
        querier: BatchQuerier,
    ) -> ScalingGroupListResult:
        """Searches scaling groups with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ScalingGroupRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.ScalingGroupRow.to_dataclass() for row in result.rows]

            return ScalingGroupListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
