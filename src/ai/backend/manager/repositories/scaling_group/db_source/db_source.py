"""Database source for scaling group repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import sqlalchemy as sa

from ai.backend.common.exception import ScalingGroupConflict
from ai.backend.manager.data.scaling_group.types import ScalingGroupData, ScalingGroupListResult
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.purger import Purger, execute_purger
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

    async def purge_scaling_group(
        self,
        purger: Purger[ScalingGroupRow],
    ) -> ScalingGroupData:
        """Purges a scaling group and all related sessions and routes using a purger.

        Cascade delete order:
        1. RoutingRow (session FK with RESTRICT)
        2. EndpointRow (resource_group FK with RESTRICT, has CASCADE to routing)
        3. SessionRow (scaling_group FK)
        4. ScalingGroupRow

        Raises ScalingGroupNotFound if scaling group doesn't exist.
        """
        async with self._db.begin_session() as session:
            scaling_group_name = purger.pk_value

            # Step 1: Find all sessions belonging to this scaling group
            session_ids_query = sa.select(SessionRow.id).where(
                SessionRow.scaling_group_name == scaling_group_name
            )
            session_ids_result = await session.execute(session_ids_query)
            session_ids = session_ids_result.scalars().all()

            # Step 2: Delete all routings associated with these sessions
            if session_ids:
                delete_routings_stmt = sa.delete(RoutingRow).where(
                    RoutingRow.session.in_(session_ids)
                )
                await session.execute(delete_routings_stmt)

            # Step 3: Delete all endpoints belonging to this scaling group
            delete_endpoints_stmt = sa.delete(EndpointRow).where(
                EndpointRow.resource_group == scaling_group_name
            )
            await session.execute(delete_endpoints_stmt)

            # Step 4: Delete all sessions belonging to this scaling group
            delete_sessions_stmt = sa.delete(SessionRow).where(
                SessionRow.scaling_group_name == scaling_group_name
            )
            await session.execute(delete_sessions_stmt)

            # Step 5: Delete the scaling group itself using purger
            result = await execute_purger(session, purger)

            if result is None:
                raise ScalingGroupNotFound(f"Scaling group not found (name:{purger.pk_value})")

            return result.row.to_dataclass()
