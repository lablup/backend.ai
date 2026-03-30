"""Database source for resource allocation repository operations."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

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
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.resource_allocation.types import (
    EffectiveAllocationData,
    KeypairContextData,
    ResourceGroupUsageData,
    ScopeUsageData,
)
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound, ScalingGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_preset.db_source.types import (
    AccessKeyFilter,
    DomainNameFilter,
    GroupIdFilter,
    ResourceOccupancyFilter,
)
from ai.backend.manager.repositories.resource_slot.types import (
    add_quantities,
    max_quantities,
    min_quantities,
    resource_slot_to_quantities,
    subtract_quantities,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourceAllocationDBSource:
    """Database source for resource allocation operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_keypair_context(self, user_id: UUID) -> KeypairContextData:
        """Resolve a user's main keypair access_key and resource_policy from DB.

        Joins users -> keypairs -> keypair_resource_policies to fetch the
        access_key and policy fields needed for resource allocation queries.
        """
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select(
                    KeyPairRow.access_key,
                    KeyPairResourcePolicyRow.total_resource_slots,
                    KeyPairResourcePolicyRow.default_for_unspecified,
                )
                .select_from(
                    sa.join(
                        UserRow,
                        KeyPairRow,
                        UserRow.main_access_key == KeyPairRow.access_key,
                    ).join(
                        KeyPairResourcePolicyRow,
                        KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name,
                    )
                )
                .where(UserRow.uuid == user_id)
            )
            result = await session.execute(query)
            row = result.first()
            if row is None:
                raise PermissionError(f"No main keypair found for user (id: {user_id})")
            return KeypairContextData(
                access_key=AccessKey(row.access_key),
                resource_policy={
                    "total_resource_slots": row.total_resource_slots,
                    "default_for_unspecified": row.default_for_unspecified,
                },
            )

    async def get_keypair_usage(
        self,
        access_key: AccessKey,
        resource_policy: Mapping[str, Any],
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ScopeUsageData:
        """Get keypair resource usage (limits, used, assignable)."""
        async with self._db.begin_readonly_session() as session:
            limits_slot = ResourceSlot.from_policy(
                resource_policy, cast(Mapping[str, Any], known_slot_types)
            )
            limits = resource_slot_to_quantities(limits_slot)
            used = await self._get_resource_occupancy(
                session, known_slot_types, filters=[AccessKeyFilter(access_key)]
            )
            assignable = subtract_quantities(limits, used)
            return ScopeUsageData(limits=limits, used=used, assignable=assignable)

    async def get_project_usage(
        self,
        project_id: UUID,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ScopeUsageData:
        """Get project resource usage by project ID (limits, used, assignable)."""
        async with self._db.begin_readonly_session() as session:
            query = sa.select(groups.c.total_resource_slots).where(groups.c.id == project_id)
            result = await session.execute(query)
            row = result.first()
            if row is None:
                raise ProjectNotFound(f"Project not found (id: {project_id})")

            project_resource_slots = row[0]
            project_resource_policy = {
                "total_resource_slots": project_resource_slots,
                "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
            }
            limits_slot = ResourceSlot.from_policy(
                project_resource_policy, cast(Mapping[str, Any], known_slot_types)
            )
            limits = resource_slot_to_quantities(limits_slot)
            used = await self._get_resource_occupancy(
                session, known_slot_types, filters=[GroupIdFilter(project_id)]
            )
            assignable = subtract_quantities(limits, used)
            return ScopeUsageData(limits=limits, used=used, assignable=assignable)

    async def get_domain_usage(
        self,
        domain_name: str,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ScopeUsageData:
        """Get domain resource usage (limits, used, assignable)."""
        async with self._db.begin_readonly_session() as session:
            query = sa.select(domains.c.total_resource_slots).where(domains.c.name == domain_name)
            result = await session.execute(query)
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
            used = await self._get_resource_occupancy(
                session, known_slot_types, filters=[DomainNameFilter(domain_name)]
            )
            assignable = subtract_quantities(limits, used)
            return ScopeUsageData(limits=limits, used=used, assignable=assignable)

    async def get_resource_group_usage(
        self,
        rg_name: str,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ResourceGroupUsageData:
        """Get resource group (scaling group) usage with max_per_node."""
        async with self._db.begin_readonly_session() as session:
            # Verify scaling group exists
            sg_exists = await session.scalar(
                sa.select(sa.exists().where(ScalingGroupRow.name == rg_name))
            )
            if not sg_exists:
                raise ScalingGroupNotFound(rg_name)

            rst = ResourceSlotTypeRow.__table__
            j = sa.join(AgentResourceRow, AgentRow, AgentResourceRow.agent_id == AgentRow.id).join(
                rst, AgentResourceRow.slot_name == rst.c.slot_name
            )
            query = (
                sa.select(
                    AgentRow.id.label("agent_id"),
                    AgentResourceRow.slot_name,
                    AgentResourceRow.capacity,
                    AgentResourceRow.used,
                    rst.c.rank,
                )
                .select_from(j)
                .where(
                    sa.and_(
                        AgentRow.scaling_group == rg_name,
                        AgentRow.schedulable == sa.true(),
                        AgentRow.status == AgentStatus.ALIVE,
                    )
                )
                .order_by(AgentRow.id, rst.c.rank)
            )
            result = await session.execute(query)
            rows = result.all()

            if not rows:
                return ResourceGroupUsageData(
                    capacity=[],
                    used=[],
                    free=[],
                    max_per_node=[],
                )

            # Build per-agent data: capacity and free slots
            agent_capacity: dict[str, list[SlotQuantity]] = {}
            agent_used: dict[str, list[SlotQuantity]] = {}
            agent_free: dict[str, list[SlotQuantity]] = {}
            for row in rows:
                aid = row.agent_id
                if aid not in agent_capacity:
                    agent_capacity[aid] = []
                    agent_used[aid] = []
                    agent_free[aid] = []
                agent_capacity[aid].append(SlotQuantity(row.slot_name, row.capacity))
                agent_used[aid].append(SlotQuantity(row.slot_name, row.used))
                agent_free[aid].append(SlotQuantity(row.slot_name, row.capacity - row.used))

            # Aggregate totals across all agents
            total_capacity: list[SlotQuantity] = []
            total_used: list[SlotQuantity] = []
            total_free: list[SlotQuantity] = []
            agent_free_list: list[list[SlotQuantity]] = []

            for aid in agent_capacity:
                total_capacity = add_quantities(total_capacity, agent_capacity[aid])
                total_used = add_quantities(total_used, agent_used[aid])
                total_free = add_quantities(total_free, agent_free[aid])
                agent_free_list.append(agent_free[aid])

            per_node_max = max_quantities(agent_free_list)

            return ResourceGroupUsageData(
                capacity=total_capacity,
                used=total_used,
                free=total_free,
                max_per_node=per_node_max,
            )

    async def get_effective_allocation(
        self,
        access_key: AccessKey,
        user_id: UUID,
        project_id: UUID,
        domain_name: str,
        resource_policy: Mapping[str, Any],
        rg_name: str,
        known_slot_types: Mapping[SlotName, SlotTypes],
        group_resource_visibility: bool,
        hide_agents: bool,
        is_admin: bool,
    ) -> EffectiveAllocationData:
        """Compute effective allocation across all scopes."""
        keypair_usage = await self.get_keypair_usage(access_key, resource_policy, known_slot_types)
        project_usage = await self.get_project_usage(project_id, known_slot_types)
        domain_usage = await self.get_domain_usage(domain_name, known_slot_types)

        # Always fetch RG data for effective calculation
        rg_usage = await self.get_resource_group_usage(rg_name, known_slot_types)

        # Build list of assignable values for min computation
        # Always include all scopes internally for accurate effective calculation
        assignable_sources = [
            keypair_usage.assignable,
            project_usage.assignable,
            domain_usage.assignable,
            rg_usage.free,
        ]
        effective_assignable = min_quantities(*assignable_sources)

        # Apply visibility rules to breakdown only (not to effective calculation)
        return EffectiveAllocationData(
            assignable=effective_assignable,
            keypair=keypair_usage,
            project=project_usage if (group_resource_visibility or is_admin) else None,
            domain=domain_usage,
            resource_group=rg_usage if (not hide_agents or is_admin) else None,
        )

    async def _get_resource_occupancy(
        self,
        db_sess: SASession,
        known_slot_types: Mapping[SlotName, SlotTypes],
        filters: list[ResourceOccupancyFilter] | None = None,
    ) -> list[SlotQuantity]:
        """Get resource occupancy with filters.

        Uses normalized resource_allocations table joined with kernels and
        resource_slot_types for rank ordering.
        Active allocations are identified by free_at IS NULL.
        """
        all_resource_statuses = (
            KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
        )
        conditions: list[Any] = [
            ResourceAllocationRow.free_at.is_(None),
            KernelRow.status.in_(all_resource_statuses),
        ]

        if filters:
            for filter_obj in filters:
                conditions.append(filter_obj.get_condition())

        rst = ResourceSlotTypeRow.__table__
        j = sa.join(
            ResourceAllocationRow, KernelRow, ResourceAllocationRow.kernel_id == KernelRow.id
        ).join(rst, ResourceAllocationRow.slot_name == rst.c.slot_name)
        effective_amount = sa.func.coalesce(
            ResourceAllocationRow.used, ResourceAllocationRow.requested
        )
        query = (
            sa.select(
                ResourceAllocationRow.slot_name,
                sa.func.sum(effective_amount).label("total"),
            )
            .select_from(j)
            .where(sa.and_(*conditions))
            .group_by(ResourceAllocationRow.slot_name, rst.c.rank)
            .order_by(rst.c.rank)
        )

        result = await db_sess.execute(query)
        quantities = [
            SlotQuantity(row.slot_name, row.total) for row in result if row.total is not None
        ]
        if not quantities:
            return [
                SlotQuantity(str(slot_name), Decimal(0)) for slot_name in known_slot_types.keys()
            ]
        return quantities
