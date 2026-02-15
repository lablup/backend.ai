"""Database source for resource preset repository operations."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.exception import ResourcePresetConflict
from ai.backend.common.types import (
    AccessKey,
    DefaultForUnspecified,
    ResourceSlot,
    SlotName,
    SlotQuantity,
    SlotTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.repository import RepositoryIntegrityError
from ai.backend.manager.errors.resource import (
    DomainNotFound,
    InvalidPresetQuery,
    ProjectNotFound,
    ResourcePresetNotFound,
    ScalingGroupNotFound,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scaling_group import query_allowed_sgroups
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.resource_preset.creators import ResourcePresetCreatorSpec
from ai.backend.manager.repositories.resource_slot.types import (
    add_quantities,
    min_quantities,
    quantities_ge,
    resource_slot_to_quantities,
    subtract_quantities,
)

from .types import (
    AccessKeyFilter,
    CheckPresetsDBData,
    DomainNameFilter,
    GroupIdFilter,
    KeypairResourceData,
    PerScalingGroupResourceData,
    PresetAllocatabilityData,
    ResourceOccupancyFilter,
    ResourceUsageData,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourcePresetDBSource:
    """Database source for resource preset operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db = db

    async def create_preset(self, creator: Creator[ResourcePresetRow]) -> ResourcePresetData:
        """
        Creates a new resource preset.
        Raises ResourcePresetConflict if a preset with the same name and scaling group already exists.
        """
        spec = cast(ResourcePresetCreatorSpec, creator.spec)
        async with self._db.begin_session() as session:
            try:
                result = await execute_creator(session, creator)
            except RepositoryIntegrityError as e:
                raise ResourcePresetConflict(
                    f"Duplicate resource preset name (name:{spec.name}, scaling_group:{spec.scaling_group_name})"
                ) from e
            return result.row.to_dataclass()

    async def get_preset_by_id(self, preset_id: UUID) -> ResourcePresetData:
        """
        Gets a resource preset by ID.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            preset_row = await self._get_preset_by_id(session, preset_id)
            if preset_row is None:
                raise ResourcePresetNotFound()
            return preset_row.to_dataclass()

    async def get_preset_by_name(self, name: str) -> ResourcePresetData:
        """
        Gets a resource preset by name.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            preset_row = await self._get_preset_by_name(session, name)
            if preset_row is None:
                raise ResourcePresetNotFound()
            return preset_row.to_dataclass()

    async def get_preset_by_id_or_name(
        self, preset_id: UUID | None, name: str | None
    ) -> ResourcePresetData:
        """
        Gets a resource preset by ID or name.
        ID takes precedence if both are provided.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            preset_row = await self._get_preset_by_id_or_name(session, preset_id, name)
            return preset_row.to_dataclass()

    async def _get_preset_by_id_or_name(
        self, db_sess: SASession, preset_id: UUID | None, name: str | None
    ) -> ResourcePresetRow:
        if preset_id is not None:
            preset_row = await self._get_preset_by_id(db_sess, preset_id)
        elif name is not None:
            preset_row = await self._get_preset_by_name(db_sess, name)
        else:
            raise InvalidPresetQuery("Either preset_id or name must be provided")

        if preset_row is None:
            raise ResourcePresetNotFound()
        return preset_row

    async def modify_preset(self, updater: Updater[ResourcePresetRow]) -> ResourcePresetData:
        """
        Modifies an existing resource preset.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        async with self._db.begin_session() as session:
            result = await execute_updater(session, updater)
            if result is None:
                raise ResourcePresetNotFound(
                    f"Resource preset with ID {updater.pk_value} not found."
                )
            return result.row.to_dataclass()

    async def delete_preset(self, preset_id: UUID | None, name: str | None) -> ResourcePresetData:
        """
        Deletes a resource preset.
        Returns the deleted preset data.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        async with self._db.begin_session() as session:
            preset_row = await self._get_preset_by_id_or_name(session, preset_id, name)
            data = preset_row.to_dataclass()
            await session.delete(preset_row)
        return data

    async def list_presets(self, scaling_group_name: str | None = None) -> list[ResourcePresetData]:
        """
        Lists all resource presets.
        If scaling_group_name is provided, returns presets for that scaling group and global presets.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(ResourcePresetRow)
            if scaling_group_name is not None:
                query = query.where(
                    sa.or_(
                        ResourcePresetRow.scaling_group_name.is_(None),
                        ResourcePresetRow.scaling_group_name == scaling_group_name,
                    )
                )
            else:
                query = query.where(ResourcePresetRow.scaling_group_name.is_(None))

            presets = []
            async for row in await session.stream_scalars(query):
                presets.append(row.to_dataclass())

        return presets

    async def check_presets_data(
        self,
        access_key: AccessKey,
        user_id: UUID,
        group_name: str,
        domain_name: str,
        resource_policy: Mapping[str, Any],
        known_slot_types: Mapping[SlotName, SlotTypes],
        scaling_group: str | None = None,
    ) -> CheckPresetsDBData:
        """
        Fetch all data needed for checking presets from database.
        This includes resource limits, occupancy, and preset allocatability.
        """
        async with self._db.begin_readonly_session() as conn:
            # Fetch all database data at once
            return await self._fetch_all_check_presets_data(
                conn,
                access_key,
                user_id,
                group_name,
                domain_name,
                resource_policy,
                known_slot_types,
                scaling_group,
            )

    async def _get_group_info(
        self,
        db_sess: SASession,
        user_id: UUID,
        group_name: str,
        domain_name: str,
    ) -> tuple[UUID, Mapping[str, str]]:
        """
        Get group ID and resource slots for a user's group.

        :param db_sess: Database session
        :param user_id: User ID
        :param group_name: Group name
        :param domain_name: Domain name
        :return: Tuple of (group_id, total_resource_slots)
        :raises ProjectNotFound: If the group does not exist or the user is not a member
        """
        j = sa.join(
            groups,
            association_groups_users,
            association_groups_users.c.group_id == groups.c.id,
        )
        query = (
            sa.select(groups.c.id, groups.c.total_resource_slots)
            .select_from(j)
            .where(
                (association_groups_users.c.user_id == user_id)
                & (groups.c.name == group_name)
                & (groups.c.domain_name == domain_name),
            )
        )
        result = await db_sess.execute(query)
        row = result.first()
        if row is None:
            raise ProjectNotFound(f"Project not found (name: {group_name})")

        return row.id, row.total_resource_slots

    async def _get_domain_resource_slots(
        self,
        db_sess: SASession,
        domain_name: str,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ResourceUsageData:
        """
        Get domain resource slots.

        :param db_sess: Database session
        :param domain_name: Domain name
        :return: ResourceUsageData with domain resource slots
        """
        query = sa.select(domains.c.total_resource_slots).where(domains.c.name == domain_name)
        result = await db_sess.execute(query)
        row = result.first()
        if row is None:
            raise DomainNotFound(f"Domain not found (name: {domain_name})")
        domain_resource_slots = row[0]
        if domain_resource_slots is None:
            raise DomainNotFound(f"Domain not found (name: {domain_name})")
        domain_resource_policy = {
            "total_resource_slots": domain_resource_slots,
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
        }
        limits_slot = ResourceSlot.from_policy(
            domain_resource_policy, cast(Mapping[str, Any], known_slot_types)
        )
        limits = resource_slot_to_quantities(limits_slot)
        occupied = await self._get_resource_occupancy(
            db_sess, known_slot_types, filters=[DomainNameFilter(domain_name)]
        )
        remaining = subtract_quantities(limits, occupied)
        return ResourceUsageData(
            limits=limits,
            occupied=occupied,
            remaining=remaining,
        )

    async def _get_user_session_occupancy_per_sgroup(
        self,
        db_sess: SASession,
        user_id: UUID,
        sgroup_names: list[str],
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> dict[str, list[SlotQuantity]]:
        """
        Get user's session resource occupancy per scaling group.

        Uses normalized resource_allocations table joined with kernels, sessions,
        and resource_slot_types for rank ordering.

        :param db_sess: Database session
        :param user_id: User ID
        :param sgroup_names: List of scaling group names
        :param known_slot_types: Known slot types for initialization
        :return: Dictionary of scaling group name to occupied resources
        """
        rst = ResourceSlotTypeRow.__table__
        j = (
            sa.join(
                ResourceAllocationRow, KernelRow, ResourceAllocationRow.kernel_id == KernelRow.id
            )
            .join(SessionRow, KernelRow.session_id == SessionRow.id)
            .join(rst, ResourceAllocationRow.slot_name == rst.c.slot_name)
        )
        query = (
            sa.select(
                SessionRow.scaling_group_name,
                ResourceAllocationRow.slot_name,
                sa.func.sum(ResourceAllocationRow.used).label("total"),
            )
            .select_from(j)
            .where(
                (KernelRow.user_uuid == user_id)
                & (ResourceAllocationRow.free_at.is_(None))
                & (SessionRow.scaling_group_name.in_(sgroup_names))
            )
            .group_by(SessionRow.scaling_group_name, ResourceAllocationRow.slot_name, rst.c.rank)
            .order_by(SessionRow.scaling_group_name, rst.c.rank)
        )
        result = await db_sess.execute(query)

        per_sgroup_occupancy: dict[str, list[SlotQuantity]] = {sg: [] for sg in sgroup_names}
        for row in result:
            if row.total is not None:
                per_sgroup_occupancy[row.scaling_group_name].append(
                    SlotQuantity(row.slot_name, row.total)
                )

        return per_sgroup_occupancy

    async def _get_agent_available_resources(
        self,
        db_sess: SASession,
        sgroup_names: list[str],
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> tuple[dict[str, list[SlotQuantity]], list[list[SlotQuantity]]]:
        """
        Get available resources from agents in given scaling groups.

        Uses normalized agent_resources table joined with resource_slot_types
        for rank ordering. Calculates remaining resources (capacity - used)
        per agent, then aggregates per scaling group.

        :param db_sess: Database session
        :param sgroup_names: List of scaling group names
        :param known_slot_types: Known slot types for initialization
        :return: Tuple of (per_sgroup_remaining, agent_slots_list)
        """
        rst = ResourceSlotTypeRow.__table__
        j = sa.join(AgentResourceRow, AgentRow, AgentResourceRow.agent_id == AgentRow.id).join(
            rst, AgentResourceRow.slot_name == rst.c.slot_name
        )
        query = (
            sa.select(
                AgentRow.id.label("agent_id"),
                AgentRow.scaling_group,
                AgentResourceRow.slot_name,
                AgentResourceRow.capacity,
                AgentResourceRow.used,
                rst.c.rank,
            )
            .select_from(j)
            .where(
                sa.and_(
                    AgentRow.scaling_group.in_(sgroup_names),
                    AgentRow.schedulable == sa.true(),
                    AgentRow.status == AgentStatus.ALIVE,
                )
            )
            .order_by(AgentRow.id, rst.c.rank)
        )
        result = await db_sess.execute(query)
        rows = result.all()

        if not rows:
            return ({sg: [] for sg in sgroup_names}, [])

        # Build remaining list[SlotQuantity] per agent, track scaling group
        agent_data: dict[str, tuple[str, list[SlotQuantity]]] = {}
        for row in rows:
            aid = row.agent_id
            if aid not in agent_data:
                agent_data[aid] = (row.scaling_group, [])
            agent_data[aid][1].append(SlotQuantity(row.slot_name, row.capacity - row.used))

        # Aggregate per scaling group
        per_sgroup_remaining: dict[str, list[SlotQuantity]] = {sg: [] for sg in sgroup_names}
        agent_slots: list[list[SlotQuantity]] = []

        for _aid, (scaling_group, remaining) in agent_data.items():
            agent_slots.append(remaining)
            if scaling_group:
                per_sgroup_remaining[scaling_group] = add_quantities(
                    per_sgroup_remaining[scaling_group], remaining
                )

        return per_sgroup_remaining, agent_slots

    async def _get_resource_occupancy(
        self,
        db_sess: SASession,
        known_slot_types: Mapping[SlotName, SlotTypes],
        filters: list[ResourceOccupancyFilter] | None = None,
    ) -> list[SlotQuantity]:
        """
        Get resource occupancy with filters.

        Uses normalized resource_allocations table joined with kernels and
        resource_slot_types for rank ordering.
        Active allocations are identified by free_at IS NULL.

        :param db_sess: Database session
        :param known_slot_types: Known slot types for initialization
        :param filters: List of filter objects to apply
        :return: Total occupied resources, rank-ordered
        """
        conditions: list[Any] = [ResourceAllocationRow.free_at.is_(None)]

        if filters:
            for filter_obj in filters:
                conditions.append(filter_obj.get_condition())

        rst = ResourceSlotTypeRow.__table__
        j = sa.join(
            ResourceAllocationRow, KernelRow, ResourceAllocationRow.kernel_id == KernelRow.id
        ).join(rst, ResourceAllocationRow.slot_name == rst.c.slot_name)
        query = (
            sa.select(
                ResourceAllocationRow.slot_name,
                sa.func.sum(ResourceAllocationRow.used).label("total"),
            )
            .select_from(j)
            .where(sa.and_(*conditions))
            .group_by(ResourceAllocationRow.slot_name, rst.c.rank)
            .order_by(rst.c.rank)
        )

        result = await db_sess.execute(query)
        return [SlotQuantity(row.slot_name, row.total) for row in result if row.total is not None]

    async def _get_keypair_resource_usage(
        self,
        db_sess: SASession,
        access_key: AccessKey,
        resource_policy: Mapping[str, Any],
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ResourceUsageData:
        """Get keypair resource usage (limits, occupied, remaining)."""
        limits_slot = ResourceSlot.from_policy(
            resource_policy, cast(Mapping[str, Any], known_slot_types)
        )
        limits = resource_slot_to_quantities(limits_slot)
        occupied = await self._get_resource_occupancy(
            db_sess, known_slot_types, filters=[AccessKeyFilter(access_key)]
        )
        remaining = subtract_quantities(limits, occupied)

        return ResourceUsageData(
            limits=limits,
            occupied=occupied,
            remaining=remaining,
        )

    async def _get_group_resource_usage(
        self,
        db_sess: SASession,
        group_id: UUID,
        group_resource_slots: Mapping[str, str],
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ResourceUsageData:
        """Get group resource usage (limits, occupied, remaining)."""
        group_resource_policy = {
            "total_resource_slots": group_resource_slots,
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
        }
        limits_slot = ResourceSlot.from_policy(
            group_resource_policy, cast(Mapping[str, Any], known_slot_types)
        )
        limits = resource_slot_to_quantities(limits_slot)
        occupied = await self._get_resource_occupancy(
            db_sess, known_slot_types, filters=[GroupIdFilter(group_id)]
        )
        remaining = subtract_quantities(limits, occupied)

        return ResourceUsageData(
            limits=limits,
            occupied=occupied,
            remaining=remaining,
        )

    async def _fetch_all_check_presets_data(
        self,
        conn: SASession,
        access_key: AccessKey,
        user_id: UUID,
        group_name: str,
        domain_name: str,
        resource_policy: Mapping[str, Any],
        known_slot_types: Mapping[SlotName, SlotTypes],
        scaling_group: str | None = None,
    ) -> CheckPresetsDBData:
        """
        Fetch all data needed for check_presets in a single method.
        """
        # Get keypair resource usage
        keypair_usage = await self._get_keypair_resource_usage(
            conn, access_key, resource_policy, known_slot_types
        )

        # Get group info and resource usage
        group_id, group_resource_slots = await self._get_group_info(
            conn, user_id, group_name, domain_name
        )
        group_usage = await self._get_group_resource_usage(
            conn, group_id, group_resource_slots, known_slot_types
        )

        # Get domain resource slots and usage
        domain_usage = await self._get_domain_resource_slots(conn, domain_name, known_slot_types)
        # Take minimum remaining resources across all scopes
        final_remaining = min_quantities(
            keypair_usage.remaining,
            group_usage.remaining,
            domain_usage.remaining,
        )

        # Get scaling groups
        # query_allowed_sgroups expects AsyncConnection, get it from session
        db_conn = await conn.connection()
        sgroups = await query_allowed_sgroups(db_conn, domain_name, group_id, str(access_key))
        sgroup_names = [sg.name for sg in sgroups]
        if scaling_group is not None:
            if scaling_group not in sgroup_names:
                raise ScalingGroupNotFound(
                    f"Scaling group not found or not allowed (name: {scaling_group})"
                )
            sgroup_names = [scaling_group]

        # Get user's session occupancy per scaling group
        per_sgroup_occupancy = await self._get_user_session_occupancy_per_sgroup(
            conn, user_id, sgroup_names, known_slot_types
        )

        # Get agent available resources per scaling group
        per_sgroup_agent_remaining, agent_slots = await self._get_agent_available_resources(
            conn, sgroup_names, known_slot_types
        )

        # Build per scaling group data
        per_sgroup: dict[str, PerScalingGroupResourceData] = {}
        empty_quantities: list[SlotQuantity] = []
        for sgname in sgroup_names:
            per_sgroup[sgname] = PerScalingGroupResourceData(
                using=per_sgroup_occupancy.get(sgname, empty_quantities),
                remaining=per_sgroup_agent_remaining.get(sgname, empty_quantities),
            )

        # Calculate total scaling group remaining
        sgroup_remaining: list[SlotQuantity] = []
        for remaining in per_sgroup_agent_remaining.values():
            sgroup_remaining = add_quantities(sgroup_remaining, remaining)

        # Apply final remaining limits to per scaling group remaining
        for sgname, sg_data in per_sgroup.items():
            sg_data.remaining = min_quantities(final_remaining, sg_data.remaining)

        sgroup_remaining = min_quantities(final_remaining, sgroup_remaining)

        # Fetch resource presets
        preset_data_list = await self.list_presets(scaling_group)

        # Check preset allocatability
        presets = []
        for preset_data in preset_data_list:
            allocatable = False
            preset_slots = resource_slot_to_quantities(
                preset_data.resource_slots.normalize_slots(ignore_unknown=True)
            )
            for agent_slot in agent_slots:
                if quantities_ge(agent_slot, preset_slots) and quantities_ge(
                    final_remaining, preset_slots
                ):
                    allocatable = True
                    break

            presets.append(
                PresetAllocatabilityData(
                    preset=preset_data,
                    allocatable=allocatable,
                )
            )

        # Build KeypairResourceData with all usage information
        keypair_data = KeypairResourceData(
            limits=keypair_usage.limits,
            occupied=keypair_usage.occupied,
            remaining=final_remaining,  # Use the minimum remaining across all scopes
            group_limits=group_usage.limits,
            group_occupied=group_usage.occupied,
            group_remaining=group_usage.remaining,
            scaling_group_remaining=sgroup_remaining,
        )

        return CheckPresetsDBData(
            known_slot_types=known_slot_types,
            keypair_data=keypair_data,
            per_sgroup_data=per_sgroup,
            presets=presets,
        )

    async def _get_preset_by_id(
        self, session: SASession, preset_id: UUID
    ) -> ResourcePresetRow | None:
        """
        Private method to get a preset by ID using an existing session.
        """
        return cast(
            ResourcePresetRow | None,
            await session.scalar(
                sa.select(ResourcePresetRow).where(ResourcePresetRow.id == preset_id)
            ),
        )

    async def _get_preset_by_name(self, session: SASession, name: str) -> ResourcePresetRow | None:
        """
        Private method to get a preset by name using an existing session.
        """
        return cast(
            ResourcePresetRow | None,
            await session.scalar(
                sa.select(ResourcePresetRow).where(ResourcePresetRow.name == name)
            ),
        )
