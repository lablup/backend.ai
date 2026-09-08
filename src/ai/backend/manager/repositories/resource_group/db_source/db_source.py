"""Database source for resource group repository operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import (
    ResourceGroupID,
    ResourceGroupName,
)
from ai.backend.common.types import SlotQuantity
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.deployment.types import DeploymentOptions
from ai.backend.manager.data.resource_group.types import (
    ResourceGroupData,
    ResourceGroupListResult,
    ResourceInfo,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.resource_group import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
    query_allowed_sgroups,
)
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.resource_slot.types import subtract_quantities

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = (
    "ResourceGroupDBSource",
    "ResourceGroupListResult",
)


class ResourceGroupDBSource:
    """
    Database source for resource group operations.
    Handles all database operations for resource groups.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db = db

    async def search_resource_groups(
        self,
        querier: BatchQuerier,
    ) -> ResourceGroupListResult:
        """Searches resource groups with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ResourceGroupRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.ResourceGroupRow.to_dataclass() for row in result.rows]

            return ResourceGroupListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def get_resource_group_id_by_name(self, name: ResourceGroupName) -> ResourceGroupID:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ResourceGroupRow.id).where(ResourceGroupRow.name == name)
            resource_group_id = await db_sess.scalar(query)
            if resource_group_id is None:
                raise ResourceGroupNotFound(name)
            return resource_group_id

    async def get_resource_group_ids_by_names(
        self,
        names: list[ResourceGroupName],
    ) -> dict[ResourceGroupName, ResourceGroupID]:
        """Resolve resource group row IDs from names; missing names are absent."""
        if not names:
            return {}
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            rows = await db_sess.execute(
                sa.select(ResourceGroupRow.name, ResourceGroupRow.id).where(
                    ResourceGroupRow.name.in_(names)
                )
            )
            return {ResourceGroupName(row.name): row.id for row in rows}

    async def get_resource_group_by_name(
        self,
        name: str,
    ) -> ResourceGroupData:
        """Get a single resource group by name (primary key).

        Args:
            name: The name of the resource group (primary key).

        Returns:
            ResourceGroupData for the requested resource group.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.get(ResourceGroupRow, name)
            if row is None:
                raise ResourceGroupNotFound(name)
            return row.to_dataclass()

    async def replace_default_deployment_options(
        self,
        name: ResourceGroupName,
        options: DeploymentOptions,
    ) -> DeploymentOptions:
        """Fully replace the ``default_deployment_options`` JSONB column
        and return the stored value in a single ``UPDATE ... RETURNING``
        round-trip.

        The column is typed as ``PydanticColumn(DeploymentOptions)`` so
        the domain model is persisted verbatim.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        async with self._db.begin_session() as session:
            stmt = (
                sa.update(ResourceGroupRow)
                .where(ResourceGroupRow.name == name)
                .values(default_deployment_options=options)
                .returning(ResourceGroupRow.default_deployment_options)
            )
            result = await session.execute(stmt)
            row = result.first()
            if row is None:
                raise ResourceGroupNotFound(f"Resource group not found (name:{name})")
            stored: DeploymentOptions = row[0]
            return stored

    async def replace_default_session_options(
        self,
        name: ResourceGroupName,
        options: DefaultSessionOptions,
    ) -> DefaultSessionOptions:
        """Fully replace the ``default_session_options`` JSONB column
        and return the stored value in a single ``UPDATE ... RETURNING``
        round-trip.

        The column is typed as ``PydanticColumn(DefaultSessionOptions)``
        so the domain model is persisted verbatim.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        async with self._db.begin_session() as session:
            stmt = (
                sa.update(ResourceGroupRow)
                .where(ResourceGroupRow.name == name)
                .values(default_session_options=options)
                .returning(ResourceGroupRow.default_session_options)
            )
            result = await session.execute(stmt)
            row = result.first()
            if row is None:
                raise ResourceGroupNotFound(f"Resource group not found (name:{name})")
            stored: DefaultSessionOptions = row[0]
            return stored

    async def check_resource_group_domain_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        domain_id: DomainID,
    ) -> bool:
        """Checks if a resource group is associated with a domain."""
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(ResourceGroupForDomainRow)
                .where(
                    sa.and_(
                        ResourceGroupForDomainRow.resource_group_id == resource_group_id,
                        ResourceGroupForDomainRow.domain_id == domain_id,
                    )
                )
            )
            result = await session.scalar(query)
            return (result or 0) > 0

    async def check_resource_group_keypair_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        access_key: str,
    ) -> bool:
        """Checks if a resource group is associated with a keypair."""
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(
                sa.exists().where(
                    sa.and_(
                        ResourceGroupForKeypairsRow.resource_group_id == resource_group_id,
                        ResourceGroupForKeypairsRow.access_key == access_key,
                    )
                )
            )
            result = await session.execute(query)
            return result.scalar() or False

    async def check_resource_group_user_group_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        user_group: uuid.UUID,
    ) -> bool:
        """Checks if a resource group is associated with a user group (project)."""
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(ResourceGroupForProjectRow)
                .where(
                    sa.and_(
                        ResourceGroupForProjectRow.resource_group_id == resource_group_id,
                        ResourceGroupForProjectRow.group == user_group,
                    )
                )
            )
            result = await session.scalar(query)
            return (result or 0) > 0

    async def list_allowed_sgroups(
        self,
        *,
        domain_name: str,
        group: str,
        access_key: str,
    ) -> list[ResourceGroupData]:
        """List allowed resource groups for a user using the legacy query_allowed_sgroups function.

        Returns ResourceGroupData for each allowed resource group.
        """
        async with self._db.begin_readonly() as conn:
            rows = await query_allowed_sgroups(conn, domain_name, group, access_key)
            # Convert raw rows to ResourceGroupData via ORM
            sg_names = [row.name for row in rows]

        if not sg_names:
            return []

        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(ResourceGroupRow)
                .where(ResourceGroupRow.name.in_(sg_names))
                .order_by(ResourceGroupRow.name)
            )
            result = await db_sess.execute(query)
            return [row.to_dataclass() for row in result.scalars()]

    async def get_resource_info(
        self,
        resource_group: str,
    ) -> ResourceInfo:
        """Get aggregated resource information for a resource group.

        Uses normalized agent_resources table with SQL-level aggregation.

        Args:
            scaling_group: The name of the resource group.

        Returns:
            ResourceInfo containing capacity, used, and free resource metrics.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        ar = AgentResourceRow.__table__
        ag = AgentRow.__table__
        rst = ResourceSlotTypeRow.__table__

        async with self._db.begin_readonly_session() as db_sess:
            # Validate resource group exists
            sg_exists = await db_sess.scalar(
                sa.select(sa.exists().where(ResourceGroupRow.name == resource_group))
            )
            if not sg_exists:
                raise ResourceGroupNotFound(resource_group)

            # Capacity: ALIVE + schedulable agents, JOIN rst for rank ordering
            capacity_stmt = (
                sa.select(ar.c.slot_name, sa.func.sum(ar.c.capacity).label("total"))
                .select_from(
                    ar.join(ag, ar.c.agent_id == ag.c.id).join(
                        rst, ar.c.slot_name == rst.c.slot_name
                    )
                )
                .where(
                    ag.c.scaling_group == resource_group,
                    ag.c.status == AgentStatus.ALIVE,
                    ag.c.schedulable == sa.true(),
                )
                .group_by(ar.c.slot_name, rst.c.rank)
                .order_by(rst.c.rank)
            )
            capacity_result = await db_sess.execute(capacity_stmt)
            capacity_list = [SlotQuantity(row.slot_name, row.total) for row in capacity_result]

            # Used: ALIVE agents (regardless of schedulable), JOIN rst for rank ordering
            used_stmt = (
                sa.select(ar.c.slot_name, sa.func.sum(ar.c.used).label("total"))
                .select_from(
                    ar.join(ag, ar.c.agent_id == ag.c.id).join(
                        rst, ar.c.slot_name == rst.c.slot_name
                    )
                )
                .where(
                    ag.c.scaling_group == resource_group,
                    ag.c.status == AgentStatus.ALIVE,
                )
                .group_by(ar.c.slot_name, rst.c.rank)
                .order_by(rst.c.rank)
            )
            used_result = await db_sess.execute(used_stmt)
            used_list = [SlotQuantity(row.slot_name, row.total) for row in used_result]

        free_list = subtract_quantities(capacity_list, used_list)

        return ResourceInfo(
            capacity=capacity_list,
            used=used_list,
            free=free_list,
        )

    # =========================================================================
    # Allow / Disallow (atomic add+remove in single read-committed transaction)
    # =========================================================================

    # =========================================================================
    # Get allowed (read-only queries)
    # =========================================================================

    async def get_allowed_domains_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
    ) -> list[str]:
        """Get allowed domain names for a resource group."""
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(DomainRow.name)
                .join(
                    ResourceGroupForDomainRow,
                    ResourceGroupForDomainRow.domain_id == DomainRow.id,
                )
                .where(ResourceGroupForDomainRow.resource_group_id == resource_group_id)
            )
            return [row[0] for row in result]

    async def get_allowed_projects_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
    ) -> list[uuid.UUID]:
        """Get allowed project IDs for a resource group."""
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(ResourceGroupForProjectRow.group).where(
                    ResourceGroupForProjectRow.resource_group_id == resource_group_id
                )
            )
            return [row[0] for row in result]

    async def get_allowed_resource_groups_for_domain(
        self,
        domain_id: DomainID,
    ) -> list[str]:
        """Get allowed resource group names for a domain."""
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(ResourceGroupRow.name)
                .join(
                    ResourceGroupForDomainRow,
                    ResourceGroupForDomainRow.resource_group_id == ResourceGroupRow.id,
                )
                .where(ResourceGroupForDomainRow.domain_id == domain_id)
            )
            return [row[0] for row in result]

    async def get_allowed_resource_groups_for_project(
        self,
        project_id: ProjectID,
    ) -> list[str]:
        """Get allowed resource group names for a project."""
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(ResourceGroupRow.name)
                .join(
                    ResourceGroupForProjectRow,
                    ResourceGroupForProjectRow.resource_group_id == ResourceGroupRow.id,
                )
                .where(ResourceGroupForProjectRow.group == project_id)
            )
            return [row[0] for row in result]
