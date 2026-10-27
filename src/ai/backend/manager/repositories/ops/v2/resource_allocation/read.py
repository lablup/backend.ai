"""Read-only resource allocation ops: the v2 read paths plus the usage reads."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import (
    DefaultForUnspecified,
    ResourceSlot,
    SessionTypes,
    SlotName,
    SlotQuantity,
    SlotTypes,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.data.resource_allocation.types import (
    ResourceGroupUsageData,
    ScopeUsageData,
    UserConcurrencyData,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.resource import (
    DomainNotFound,
    ProjectNotFound,
    ResourceGroupNotFound,
)
from ai.backend.manager.errors.user import KeyPairNotFound
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.resource_policy.searchable_fields import (
    KeyPairResourcePolicySearchableFields,
)
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.repositories.resource_preset.db_source.types import (
    DomainNameFilter,
    GroupIdFilter,
    NonPrivateSessionFilter,
    ResourceOccupancyFilter,
    UserIdFilter,
)
from ai.backend.manager.repositories.resource_slot.types import (
    add_quantities,
    max_quantities,
    resource_slot_to_quantities,
    subtract_quantities,
)


class ResourceAllocationReadOps(V2ReadOps):
    """The general v2 read ops plus the resource allocation usage reads."""

    async def user_usage(self, user_id: UserID) -> ScopeUsageData:
        """A user's usage across all their keypairs, counted as the scheduler does."""
        known_slot_types = await self._known_slot_types()
        resource_policy = await self._default_keypair_resource_policy(user_id)
        limits = self._limits_from_policy(
            resource_policy.total_resource_slots,
            resource_policy.default_for_unspecified,
            known_slot_types,
        )
        used = await self._resource_occupancy(
            known_slot_types,
            filters=[UserIdFilter(user_id), NonPrivateSessionFilter()],
        )
        return ScopeUsageData(
            limits=limits,
            used=used,
            assignable=subtract_quantities(limits, used),
        )

    async def user_concurrency(self, user_id: UserID) -> UserConcurrencyData:
        """Count the user's active sessions with the scheduler's concurrency-check conditions."""
        is_private = SessionRow.session_type.in_(SessionTypes.private_types())
        row = (
            await self._sess.execute(
                sa.select(
                    sa.func.count().filter(~is_private).label("session_count"),
                    sa.func.count().filter(is_private).label("private_session_count"),
                ).where(
                    SessionRow.user_uuid == user_id,
                    SessionRow.status.in_(SessionStatus.resource_occupied_statuses()),
                )
            )
        ).one()
        return UserConcurrencyData(
            session_count=row.session_count,
            private_session_count=row.private_session_count,
        )

    async def project_usage(self, project_id: UUID) -> ScopeUsageData:
        """The usage of a project."""
        known_slot_types = await self._known_slot_types()
        row = (
            await self._sess.execute(
                sa.select(ProjectRow.total_resource_slots).where(ProjectRow.id == project_id)
            )
        ).first()
        if row is None:
            raise ProjectNotFound(f"Project not found (id: {project_id})")
        limits = self._limits_from_policy(
            row.total_resource_slots, DefaultForUnspecified.UNLIMITED, known_slot_types
        )
        used = await self._resource_occupancy(known_slot_types, filters=[GroupIdFilter(project_id)])
        return ScopeUsageData(
            limits=limits,
            used=used,
            assignable=subtract_quantities(limits, used),
        )

    async def domain_usage(self, domain_name: str) -> ScopeUsageData:
        """The usage of a domain."""
        known_slot_types = await self._known_slot_types()
        row = (
            await self._sess.execute(
                sa.select(DomainRow.total_resource_slots).where(DomainRow.name == domain_name)
            )
        ).first()
        if row is None or row.total_resource_slots is None:
            raise DomainNotFound(f"Domain not found (name: {domain_name})")
        limits = self._limits_from_policy(
            row.total_resource_slots, DefaultForUnspecified.UNLIMITED, known_slot_types
        )
        used = await self._resource_occupancy(
            known_slot_types, filters=[DomainNameFilter(domain_name)]
        )
        return ScopeUsageData(
            limits=limits,
            used=used,
            assignable=subtract_quantities(limits, used),
        )

    async def resource_group_usage(self, rg_name: str) -> ResourceGroupUsageData:
        """Resource group capacity and usage, with the largest free amount on one agent."""
        sg_exists = await self._sess.scalar(
            sa.select(sa.exists().where(ResourceGroupRow.name == rg_name))
        )
        if not sg_exists:
            raise ResourceGroupNotFound(rg_name)

        j = sa.join(AgentResourceRow, AgentRow, AgentResourceRow.agent_id == AgentRow.id).join(
            ResourceSlotTypeRow, AgentResourceRow.slot_name == ResourceSlotTypeRow.slot_name
        )
        query = (
            sa.select(
                AgentRow.id.label("agent_id"),
                AgentResourceRow.slot_name,
                AgentResourceRow.capacity,
                AgentResourceRow.used,
                ResourceSlotTypeRow.rank,
            )
            .select_from(j)
            .where(
                sa.and_(
                    AgentRow.scaling_group == rg_name,
                    AgentRow.schedulable == sa.true(),
                    AgentRow.status == AgentStatus.ALIVE,
                )
            )
            .order_by(AgentRow.id, ResourceSlotTypeRow.rank)
        )
        rows = (await self._sess.execute(query)).all()

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

        return ResourceGroupUsageData(
            capacity=total_capacity,
            used=total_used,
            free=total_free,
            max_per_node=max_quantities(agent_free_list),
        )

    async def _known_slot_types(self) -> Mapping[SlotName, SlotTypes]:
        """The enabled slot types in the resource_slot_types registry, as the scheduler reads them."""
        rows = (
            await self._sess.execute(
                sa.select(ResourceSlotTypeRow.slot_name, ResourceSlotTypeRow.slot_type).where(
                    ResourceSlotTypeRow.enabled.is_(True)
                )
            )
        ).all()
        return {SlotName(row.slot_name): SlotTypes(row.slot_type) for row in rows}

    async def _default_keypair_resource_policy(self, user_id: UserID) -> KeyPairResourcePolicyData:
        """The resource policy of the user's default keypair."""
        row = await self._sess.scalar(
            sa.select(KeyPairResourcePolicyRow)
            .join(KeyPairRow, KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name)
            .where(KeyPairRow.user == user_id, KeyPairRow.is_default)
        )
        if row is None:
            raise KeyPairNotFound(f"User {user_id} holds no default keypair")
        return KeyPairResourcePolicySearchableFields.own.to_data(row)

    def _limits_from_policy(
        self,
        total_resource_slots: ResourceSlot,
        default_for_unspecified: DefaultForUnspecified,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> list[SlotQuantity]:
        """Resolve a scope's total_resource_slots into per-slot limits."""
        slot_types = {str(name): slot_type for name, slot_type in known_slot_types.items()}
        limits_slot = ResourceSlot.from_policy(
            {
                "total_resource_slots": total_resource_slots,
                "default_for_unspecified": default_for_unspecified,
            },
            slot_types,
        )
        return resource_slot_to_quantities(limits_slot)

    async def _resource_occupancy(
        self,
        known_slot_types: Mapping[SlotName, SlotTypes],
        filters: list[ResourceOccupancyFilter] | None = None,
    ) -> list[SlotQuantity]:
        """Get resource occupancy with filters.

        Active allocations are identified by free_at IS NULL.
        """
        all_resource_statuses = (
            KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
        )
        conditions: list[sa.ColumnElement[bool]] = [
            ResourceAllocationRow.free_at.is_(None),
            KernelRow.status.in_(all_resource_statuses),
        ]

        if filters:
            for filter_obj in filters:
                conditions.append(filter_obj.get_condition())

        j = sa.join(
            ResourceAllocationRow, KernelRow, ResourceAllocationRow.kernel_id == KernelRow.id
        ).join(
            ResourceSlotTypeRow, ResourceAllocationRow.slot_name == ResourceSlotTypeRow.slot_name
        )
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
            .group_by(ResourceAllocationRow.slot_name, ResourceSlotTypeRow.rank)
            .order_by(ResourceSlotTypeRow.rank)
        )

        result = await self._sess.execute(query)
        quantities = [
            SlotQuantity(row.slot_name, row.total) for row in result if row.total is not None
        ]
        if not quantities:
            return [
                SlotQuantity(str(slot_name), Decimal(0)) for slot_name in known_slot_types.keys()
            ]
        return quantities
