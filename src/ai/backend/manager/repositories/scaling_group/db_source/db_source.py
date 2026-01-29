"""Database source for scaling group repository operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, cast

import sqlalchemy as sa

from ai.backend.common.exception import ScalingGroupConflict
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.scaling_group.types import (
    ResourceInfo,
    ScalingGroupData,
    ScalingGroupListResult,
)
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import (
    BulkCreator,
    Creator,
    execute_bulk_creator,
    execute_creator,
)
from ai.backend.manager.repositories.base.purger import (
    BatchPurger,
    Purger,
    execute_batch_purger,
    execute_purger,
)
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
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
            except sa.exc.IntegrityError as e:
                spec = cast(ScalingGroupCreatorSpec, creator.spec)
                raise ScalingGroupConflict(f"Duplicate scaling group name: {spec.name}") from e
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

    async def get_scaling_group_by_name(
        self,
        name: str,
    ) -> ScalingGroupData:
        """Get a single scaling group by name (primary key).

        Args:
            name: The name of the scaling group (primary key).

        Returns:
            ScalingGroupData for the requested scaling group.

        Raises:
            ScalingGroupNotFound: If the scaling group does not exist.
        """
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.get(ScalingGroupRow, name)
            if row is None:
                raise ScalingGroupNotFound(name)
            return row.to_dataclass()

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

    async def update_scaling_group(
        self,
        updater: Updater[ScalingGroupRow],
    ) -> ScalingGroupData:
        """Updates an existing scaling group.

        Raises ScalingGroupNotFound if the scaling group does not exist.
        """
        async with self._db.begin_session() as session:
            result = await execute_updater(session, updater)
            if result is None:
                raise ScalingGroupNotFound(f"Scaling group not found (name:{updater.pk_value})")
            return result.row.to_dataclass()

    async def associate_scaling_group_with_domains(
        self,
        bulk_creator: BulkCreator[ScalingGroupForDomainRow],
    ) -> None:
        """Associates a scaling group with multiple domains."""
        async with self._db.begin_session() as session:
            await execute_bulk_creator(session, bulk_creator)

    async def disassociate_scaling_group_with_domains(
        self,
        purger: BatchPurger[ScalingGroupForDomainRow],
    ) -> None:
        """Disassociates a scaling group from multiple domains."""
        async with self._db.begin_session() as session:
            await execute_batch_purger(session, purger)

    async def check_scaling_group_domain_association_exists(
        self,
        scaling_group: str,
        domain: str,
    ) -> bool:
        """Checks if a scaling group is associated with a domain."""
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(ScalingGroupForDomainRow)
                .where(
                    sa.and_(
                        ScalingGroupForDomainRow.scaling_group == scaling_group,
                        ScalingGroupForDomainRow.domain == domain,
                    )
                )
            )
            result = await session.scalar(query)
            return (result or 0) > 0

    async def associate_scaling_group_with_keypairs(
        self,
        bulk_creator: BulkCreator[ScalingGroupForKeypairsRow],
    ) -> None:
        """Associates a scaling group with multiple keypairs."""
        async with self._db.begin_session() as session:
            await execute_bulk_creator(session, bulk_creator)

    async def disassociate_scaling_group_with_keypairs(
        self,
        purger: BatchPurger[ScalingGroupForKeypairsRow],
    ) -> None:
        """Disassociates a scaling group from multiple keypairs."""
        async with self._db.begin_session() as session:
            await execute_batch_purger(session, purger)

    async def check_scaling_group_keypair_association_exists(
        self,
        scaling_group_name: str,
        access_key: str,
    ) -> bool:
        """Checks if a scaling group is associated with a keypair."""
        async with self._db.begin_readonly_session() as session:
            query = sa.select(
                sa.exists().where(
                    sa.and_(
                        ScalingGroupForKeypairsRow.scaling_group == scaling_group_name,
                        ScalingGroupForKeypairsRow.access_key == access_key,
                    )
                )
            )
            result = await session.execute(query)
            return result.scalar() or False

    async def associate_scaling_group_with_user_groups(
        self,
        bulk_creator: BulkCreator[ScalingGroupForProjectRow],
    ) -> None:
        """Associates a scaling group with multiple user groups (projects)."""
        async with self._db.begin_session() as session:
            await execute_bulk_creator(session, bulk_creator)

    async def disassociate_scaling_group_with_user_groups(
        self,
        purger: BatchPurger[ScalingGroupForProjectRow],
    ) -> None:
        """Disassociates a single scaling group from a user group (project)."""
        async with self._db.begin_session() as session:
            await execute_batch_purger(session, purger)

    async def check_scaling_group_user_group_association_exists(
        self,
        scaling_group: str,
        user_group: uuid.UUID,
    ) -> bool:
        """Checks if a scaling group is associated with a user group (project)."""
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(ScalingGroupForProjectRow)
                .where(
                    sa.and_(
                        ScalingGroupForProjectRow.scaling_group == scaling_group,
                        ScalingGroupForProjectRow.group == user_group,
                    )
                )
            )
            result = await session.scalar(query)
            return (result or 0) > 0

    async def get_resource_info(
        self,
        scaling_group: str,
    ) -> ResourceInfo:
        """Get aggregated resource information for a scaling group.

        Args:
            scaling_group: The name of the scaling group.

        Returns:
            ResourceInfo containing capacity, used, and free resource metrics.

        Raises:
            ScalingGroupNotFound: If the scaling group does not exist.
        """
        async with self._db.begin_readonly_session() as db_sess:
            # Validate scaling group exists
            sg_exists = await db_sess.scalar(
                sa.select(sa.exists().where(ScalingGroupRow.name == scaling_group))
            )
            if not sg_exists:
                raise ScalingGroupNotFound(scaling_group)

            # Get capacity from ALIVE, schedulable agents
            capacity_query = sa.select(AgentRow.available_slots).where(
                sa.and_(
                    AgentRow.scaling_group == scaling_group,
                    AgentRow.status == AgentStatus.ALIVE,
                    AgentRow.schedulable == sa.true(),
                )
            )
            capacity_result = await db_sess.execute(capacity_query)
            capacity = ResourceSlot()
            for row in capacity_result:
                if row.available_slots:
                    capacity = capacity + row.available_slots

            # Get used from kernels in RUNNING/TERMINATING status
            used_query = sa.select(KernelRow.occupied_slots).where(
                sa.and_(
                    KernelRow.scaling_group == scaling_group,
                    KernelRow.status.in_(KernelStatus.resource_occupied_statuses()),
                )
            )
            used_result = await db_sess.execute(used_query)
            used = ResourceSlot()
            for row in used_result:
                if row.occupied_slots:
                    used = used + row.occupied_slots

            # Calculate free = capacity - used
            free = capacity - used

            return ResourceInfo(
                capacity=capacity,
                used=used,
                free=free,
            )
