"""Database source for resource preset repository operations."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Mapping, Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.exception import InvalidAPIParameters, ResourcePresetConflict
from ai.backend.common.types import (
    AccessKey,
    DefaultForUnspecified,
    ResourceSlot,
    SlotName,
    SlotTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.resource import ResourcePresetNotFound
from ai.backend.manager.models import (
    AgentRow,
    AgentStatus,
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
    CheckPresetsDBData,
    KeypairResourceData,
    PerScalingGroupResourceData,
    PresetAllocatabilityData,
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

    async def get_keypair_occupancy(
        self, access_key: AccessKey, db_sess: SASession
    ) -> ResourceSlot:
        """Get keypair resource occupancy."""
        query = sa.select([KernelRow.occupied_slots]).where(
            (KernelRow.access_key == access_key)
            & (KernelRow.status.in_(KernelStatus.resource_occupied_statuses()))
        )
        total = ResourceSlot()
        async for row in await db_sess.stream(query):
            if row[0]:  # occupied_slots might be null
                total += row[0]
        return total

    async def get_group_occupancy(self, group_id: UUID, db_sess: SASession) -> ResourceSlot:
        """Get group resource occupancy."""
        query = sa.select([KernelRow.occupied_slots]).where(
            (KernelRow.group_id == group_id)
            & (KernelRow.status.in_(KernelStatus.resource_occupied_statuses()))
        )
        total = ResourceSlot()
        async for row in await db_sess.stream(query):
            if row[0]:  # occupied_slots might be null
                total += row[0]
        return total

    async def get_domain_occupancy(self, domain_name: str, db_sess: SASession) -> ResourceSlot:
        """Get domain resource occupancy."""
        query = sa.select([KernelRow.occupied_slots]).where(
            (KernelRow.domain_name == domain_name)
            & (KernelRow.status.in_(KernelStatus.resource_occupied_statuses()))
        )
        total = ResourceSlot()
        async for row in await db_sess.stream(query):
            if row[0]:  # occupied_slots might be null
                total += row[0]
        return total

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
        # Calculate keypair limits and occupancy
        keypair_limits = ResourceSlot.from_policy(resource_policy, known_slot_types)
        keypair_occupied = await self.get_keypair_occupancy(access_key, conn)
        keypair_remaining = keypair_limits - keypair_occupied

        # Get group data
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
        result = await conn.execute(query)
        row = result.first()
        if row is None:
            raise InvalidAPIParameters(f"Unknown project (name: {group_name})")

        group_id = row["id"]
        group_resource_slots = row["total_resource_slots"]
        group_resource_policy = {
            "total_resource_slots": group_resource_slots,
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
        }
        group_limits = ResourceSlot.from_policy(group_resource_policy, known_slot_types)
        group_occupied = await self.get_group_occupancy(group_id, conn)
        group_remaining = group_limits - group_occupied

        # Get domain data
        query = sa.select([domains.c.total_resource_slots]).where(domains.c.name == domain_name)
        domain_resource_slots = await conn.scalar(query)
        domain_resource_policy = {
            "total_resource_slots": domain_resource_slots,
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
        }
        domain_limits = ResourceSlot.from_policy(domain_resource_policy, known_slot_types)
        domain_occupied = await self.get_domain_occupancy(domain_name, conn)
        domain_remaining = domain_limits - domain_occupied

        # Take minimum remaining resources
        for slot in known_slot_types:
            keypair_remaining[slot] = min(
                keypair_remaining[slot],
                group_remaining[slot],
                domain_remaining[slot],
            )

        # Get scaling groups
        sgroups = await query_allowed_sgroups(conn, domain_name, group_id, access_key)
        sgroup_names = [sg.name for sg in sgroups]
        if scaling_group is not None:
            if scaling_group not in sgroup_names:
                raise InvalidAPIParameters("Unknown scaling group")
            sgroup_names = [scaling_group]

        # Initialize per scaling group data
        per_sgroup = {
            sgname: PerScalingGroupResourceData(
                using=ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()}),
                remaining=ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()}),
            )
            for sgname in sgroup_names
        }

        # Get per scaling group resource usage
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
        async for row in await conn.stream(query):
            per_sgroup[row["scaling_group_name"]].using += row["occupied_slots"]

        # Get per scaling group resource remaining from agents
        sgroup_remaining = ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()})
        query = (
            sa.select([
                AgentRow.available_slots,
                AgentRow.occupied_slots,
                AgentRow.scaling_group,
            ])
            .select_from(AgentRow)
            .where(
                (AgentRow.status == AgentStatus.ALIVE) & (AgentRow.scaling_group.in_(sgroup_names)),
            )
        )
        agent_slots = []
        async for row in await conn.stream(query):
            remaining = row["available_slots"] - row["occupied_slots"]
            remaining += ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()})
            sgroup_remaining += remaining
            agent_slots.append(remaining)
            per_sgroup[row["scaling_group"]].remaining += remaining

        # Apply keypair limits to per scaling group remaining
        for sgname, sg_data in per_sgroup.items():
            for slot in known_slot_types.keys():
                if slot in sg_data.remaining:
                    sg_data.remaining[slot] = min(keypair_remaining[slot], sg_data.remaining[slot])

        for slot in known_slot_types.keys():
            sgroup_remaining[slot] = min(keypair_remaining[slot], sgroup_remaining[slot])

        # Fetch resource presets
        preset_data_list = await self.list_presets(scaling_group)

        # Check preset allocatability
        presets = []
        for preset_data in preset_data_list:
            allocatable = False
            preset_slots = preset_data.resource_slots.normalize_slots(ignore_unknown=True)
            for agent_slot in agent_slots:
                if agent_slot >= preset_slots and keypair_remaining >= preset_slots:
                    allocatable = True
                    break

            presets.append(
                PresetAllocatabilityData(
                    preset=preset_data,
                    allocatable=allocatable,
                )
            )

        keypair_data = KeypairResourceData(
            limits=keypair_limits,
            occupied=keypair_occupied,
            remaining=keypair_remaining,
            group_limits=group_limits,
            group_occupied=group_occupied,
            group_remaining=group_remaining,
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
