"""Database source for resource preset repository operations."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Mapping, Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.exception import ResourcePresetConflict
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    DefaultForUnspecified,
    ResourceSlot,
    SlotName,
    SlotTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.resource import (
    DomainNotFound,
    ProjectNotFound,
    ResourcePresetNotFound,
    ScalingGroupNotFound,
)
from ai.backend.manager.models import (
    AgentRow,
    KernelRow,
    SessionRow,
    association_groups_users,
    domains,
    groups,
    query_allowed_sgroups,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.resource_preset.types import (
    ResourcePresetCreator,
    ResourcePresetModifier,
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

    async def create_preset(self, creator: ResourcePresetCreator) -> ResourcePresetData:
        """
        Creates a new resource preset.
        Raises ResourcePresetConflict if a preset with the same name and scaling group already exists.
        """
        async with self._db.begin_session() as session:
            preset_row = await ResourcePresetRow.create(creator, db_session=session)
            if preset_row is None:
                raise ResourcePresetConflict(
                    f"Duplicate resource preset name (name:{creator.name}, scaling_group:{creator.scaling_group_name})"
                )
            data = preset_row.to_dataclass()
        return data

    async def get_preset_by_id(self, preset_id: UUID) -> ResourcePresetData:
        """
        Gets a resource preset by ID.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        async with self._db.begin_readonly_session() as session:
            preset_row = await self._get_preset_by_id(session, preset_id)
            if preset_row is None:
                raise ResourcePresetNotFound()
            data = preset_row.to_dataclass()
        return data

    async def get_preset_by_name(self, name: str) -> ResourcePresetData:
        """
        Gets a resource preset by name.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        async with self._db.begin_readonly_session() as session:
            preset_row = await self._get_preset_by_name(session, name)
            if preset_row is None:
                raise ResourcePresetNotFound()
            data = preset_row.to_dataclass()
        return data

    async def get_preset_by_id_or_name(
        self, preset_id: Optional[UUID], name: Optional[str]
    ) -> ResourcePresetData:
        """
        Gets a resource preset by ID or name.
        ID takes precedence if both are provided.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        async with self._db.begin_readonly_session() as session:
            preset_row = await self._get_preset_by_id_or_name(session, preset_id, name)
            data = preset_row.to_dataclass()
        return data

    async def _get_preset_by_id_or_name(
        self, db_sess: SASession, preset_id: Optional[UUID], name: Optional[str]
    ) -> ResourcePresetRow:
        if preset_id is not None:
            preset_row = await self._get_preset_by_id(db_sess, preset_id)
        elif name is not None:
            preset_row = await self._get_preset_by_name(db_sess, name)
        else:
            raise ValueError("Either preset_id or name must be provided")

        if preset_row is None:
            raise ResourcePresetNotFound()
        return preset_row

    async def modify_preset(
        self, preset_id: Optional[UUID], name: Optional[str], modifier: ResourcePresetModifier
    ) -> ResourcePresetData:
        """
        Modifies an existing resource preset.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        async with self._db.begin_session() as session:
            preset_row = await self._get_preset_by_id_or_name(session, preset_id, name)
            to_update = modifier.fields_to_update()
            for key, value in to_update.items():
                setattr(preset_row, key, value)
            await session.flush()
            data = preset_row.to_dataclass()
        return data

    async def delete_preset(
        self, preset_id: Optional[UUID], name: Optional[str]
    ) -> ResourcePresetData:
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

    async def list_presets(
        self, scaling_group_name: Optional[str] = None
    ) -> list[ResourcePresetData]:
        """
        Lists all resource presets.
        If scaling_group_name is provided, returns presets for that scaling group and global presets.
        """
        async with self._db.begin_readonly_session() as session:
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
        resource_policy: Mapping[str, str],
        known_slot_types: Mapping[SlotName, SlotTypes],
        scaling_group: Optional[str] = None,
    ) -> CheckPresetsDBData:
        """
        Fetch all data needed for checking presets from database.
        This includes resource limits, occupancy, and preset allocatability.
        """
        async with self._db.begin_readonly_session() as conn:
            # Fetch all database data at once
            db_data = await self._fetch_all_check_presets_data(
                conn,
                access_key,
                user_id,
                group_name,
                domain_name,
                resource_policy,
                known_slot_types,
                scaling_group,
            )

        return db_data

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
            sa.select([groups.c.id, groups.c.total_resource_slots])
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

        return row["id"], row["total_resource_slots"]

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
        query = sa.select([domains.c.total_resource_slots]).where(domains.c.name == domain_name)
        result = await db_sess.execute(query)
        domain_resource_slots = result.first()[0]
        if domain_resource_slots is None:
            raise DomainNotFound(f"Domain not found (name: {domain_name})")
        domain_resource_policy = {
            "total_resource_slots": domain_resource_slots,
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
        }
        limits = ResourceSlot.from_policy(domain_resource_policy, known_slot_types)
        occupied = await self._get_resource_occupancy(
            db_sess, known_slot_types, filters=[DomainNameFilter(domain_name)]
        )
        remaining = limits - occupied
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
    ) -> dict[str, ResourceSlot]:
        """
        Get user's session resource occupancy per scaling group.

        :param db_sess: Database session
        :param user_id: User ID
        :param sgroup_names: List of scaling group names
        :param known_slot_types: Known slot types for initialization
        :return: Dictionary of scaling group name to occupied resources
        """
        per_sgroup_occupancy = {
            sgname: ResourceSlot.from_known_slots(known_slot_types) for sgname in sgroup_names
        }

        j = sa.join(KernelRow, SessionRow, KernelRow.session_id == SessionRow.id)
        query = (
            sa.select([KernelRow.occupied_slots, SessionRow.scaling_group_name])
            .select_from(j)
            .where(
                (KernelRow.user_uuid == user_id)
                & (KernelRow.status.in_(KernelStatus.resource_occupied_statuses()))
                & (SessionRow.scaling_group_name.in_(sgroup_names)),
            )
        )
        async for row in await db_sess.stream(query):
            if row["occupied_slots"]:
                per_sgroup_occupancy[row["scaling_group_name"]] += row["occupied_slots"]

        return per_sgroup_occupancy

    async def _get_agent_available_resources(
        self,
        db_sess: SASession,
        sgroup_names: list[str],
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> tuple[dict[str, ResourceSlot], list[ResourceSlot]]:
        """
        Get available resources from agents in given scaling groups.

        Calculate actual occupied slots by aggregating from kernels with
        resource_occupied_statuses (RUNNING, TERMINATING) instead of using
        the cached AgentRow.occupied_slots value.

        Uses two efficient queries: one for agents, and one for filtered kernels
        only with resource_occupied_statuses to minimize data loading.

        :param db_sess: Database session
        :param sgroup_names: List of scaling group names
        :param known_slot_types: Known slot types for initialization
        :return: Tuple of (per_sgroup_remaining, agent_slots_list)
        """
        # Query 1: Get agents in the scaling groups
        agent_query = sa.select(AgentRow).where(
            sa.and_(
                AgentRow.scaling_group.in_(sgroup_names),
                AgentRow.available_slots.isnot(None),
                AgentRow.schedulable == sa.true(),
                AgentRow.status == AgentStatus.ALIVE,
            )
        )

        agent_result = await db_sess.execute(agent_query)
        agent_rows = list(agent_result.scalars().all())

        if not agent_rows:
            # No agents found, return empty results
            return (
                {
                    sgname: ResourceSlot.from_known_slots(known_slot_types)
                    for sgname in sgroup_names
                },
                [],
            )

        # Query 2: Get only kernels with resource_occupied_statuses for these agents
        agent_ids = [agent.id for agent in agent_rows]
        kernel_query = sa.select(KernelRow.agent, KernelRow.occupied_slots).where(
            sa.and_(
                KernelRow.agent.in_(agent_ids),
                KernelRow.status.in_(KernelStatus.resource_occupied_statuses()),
            )
        )

        kernel_result = await db_sess.execute(kernel_query)

        # Aggregate occupied slots by agent
        agent_occupied: dict[AgentId, ResourceSlot] = defaultdict(
            lambda: ResourceSlot.from_known_slots(known_slot_types)
        )
        for row in kernel_result:
            if row.agent and row.occupied_slots:
                agent_occupied[row.agent] += row.occupied_slots

        # Calculate remaining resources per agent and per scaling group
        per_sgroup_remaining = {
            sgname: ResourceSlot.from_known_slots(known_slot_types) for sgname in sgroup_names
        }
        agent_slots = []

        for agent in agent_rows:
            actual_occupied = agent_occupied[agent.id]
            remaining = agent.available_slots - actual_occupied
            agent_slots.append(remaining)
            per_sgroup_remaining[agent.scaling_group] += remaining

        return per_sgroup_remaining, agent_slots

    async def _get_resource_occupancy(
        self,
        db_sess: SASession,
        known_slot_types: Mapping[SlotName, SlotTypes],
        filters: list[ResourceOccupancyFilter] | None = None,
    ) -> ResourceSlot:
        """
        Get resource occupancy with filters.

        :param db_sess: Database session
        :param known_slot_types: Known slot types for initialization
        :param filters: List of filter objects to apply
        :return: Total occupied resources
        """
        conditions = [KernelRow.status.in_(KernelStatus.resource_occupied_statuses())]

        if filters:
            for filter_obj in filters:
                conditions.append(filter_obj.get_condition())

        query = sa.select([KernelRow.occupied_slots]).where(sa.and_(*conditions))

        total = ResourceSlot.from_known_slots(known_slot_types)
        async for row in await db_sess.stream(query):
            if row[0]:  # occupied_slots might be null
                total += row[0]
        return total

    async def _get_keypair_resource_usage(
        self,
        db_sess: SASession,
        access_key: AccessKey,
        resource_policy: Mapping[str, str],
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ResourceUsageData:
        """Get keypair resource usage (limits, occupied, remaining)."""
        limits = ResourceSlot.from_policy(resource_policy, known_slot_types)
        occupied = await self._get_resource_occupancy(
            db_sess, known_slot_types, filters=[AccessKeyFilter(access_key)]
        )
        remaining = limits - occupied

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
        limits = ResourceSlot.from_policy(group_resource_policy, known_slot_types)
        occupied = await self._get_resource_occupancy(
            db_sess, known_slot_types, filters=[GroupIdFilter(group_id)]
        )
        remaining = limits - occupied

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
        resource_policy: Mapping[str, str],
        known_slot_types: Mapping[SlotName, SlotTypes],
        scaling_group: Optional[str] = None,
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
        final_remaining = ResourceSlot.from_known_slots(known_slot_types)
        for slot in known_slot_types:
            final_remaining[slot] = min(
                keypair_usage.remaining[slot],
                group_usage.remaining[slot],
                domain_usage.remaining[slot],
            )

        # Get scaling groups
        sgroups = await query_allowed_sgroups(conn, domain_name, group_id, access_key)
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
        per_sgroup = {}
        empty_slot = ResourceSlot.from_known_slots(known_slot_types)
        for sgname in sgroup_names:
            per_sgroup[sgname] = PerScalingGroupResourceData(
                using=per_sgroup_occupancy.get(sgname, empty_slot),
                remaining=per_sgroup_agent_remaining.get(sgname, empty_slot),
            )

        # Calculate total scaling group remaining
        sgroup_remaining = ResourceSlot.from_known_slots(known_slot_types)
        for remaining in per_sgroup_agent_remaining.values():
            sgroup_remaining += remaining

        # Apply final remaining limits to per scaling group remaining
        for sgname, sg_data in per_sgroup.items():
            for slot in known_slot_types.keys():
                if slot in sg_data.remaining:
                    sg_data.remaining[slot] = min(final_remaining[slot], sg_data.remaining[slot])

        for slot in known_slot_types.keys():
            sgroup_remaining[slot] = min(final_remaining[slot], sgroup_remaining[slot])

        # Fetch resource presets
        preset_data_list = await self.list_presets(scaling_group)

        # Check preset allocatability
        presets = []
        for preset_data in preset_data_list:
            allocatable = False
            preset_slots = preset_data.resource_slots.normalize_slots(ignore_unknown=True)
            for agent_slot in agent_slots:
                if agent_slot >= preset_slots and final_remaining >= preset_slots:
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
    ) -> Optional[ResourcePresetRow]:
        """
        Private method to get a preset by ID using an existing session.
        """
        return await session.scalar(
            sa.select(ResourcePresetRow).where(ResourcePresetRow.id == preset_id)
        )

    async def _get_preset_by_name(
        self, session: SASession, name: str
    ) -> Optional[ResourcePresetRow]:
        """
        Private method to get a preset by name using an existing session.
        """
        return await session.scalar(
            sa.select(ResourcePresetRow).where(ResourcePresetRow.name == name)
        )
