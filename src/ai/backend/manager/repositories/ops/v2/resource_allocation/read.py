"""Read-only resource allocation ops: the v2 read paths plus the usage reads."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any, cast

import sqlalchemy as sa

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import (
    ResourceSlot,
    SlotName,
    SlotQuantity,
    SlotTypes,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.data.resource_allocation.types import ScopeUsageData
from ai.backend.manager.errors.user import KeyPairNotFound
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.resource_policy.searchable_fields import (
    KeyPairResourcePolicySearchableFields,
)
from ai.backend.manager.models.resource_slot.row import (
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.repositories.resource_preset.db_source.types import (
    NonPrivateSessionFilter,
    ResourceOccupancyFilter,
    UserIdFilter,
)
from ai.backend.manager.repositories.resource_slot.types import (
    resource_slot_to_quantities,
    subtract_quantities,
)


class ResourceAllocationReadOps(V2ReadOps):
    """The general v2 read ops plus the resource allocation usage reads."""

    async def user_usage(self, user_id: UserID) -> ScopeUsageData:
        """A user's usage across all their keypairs, counted as the scheduler does."""
        known_slot_types = await self._known_slot_types()
        resource_policy = await self._default_keypair_resource_policy(user_id)
        limits = self._limits_from_policy(resource_policy, known_slot_types)
        used = await self._resource_occupancy(
            known_slot_types,
            filters=[UserIdFilter(user_id), NonPrivateSessionFilter()],
        )
        return ScopeUsageData(
            limits=limits,
            used=used,
            assignable=subtract_quantities(limits, used),
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
        resource_policy: KeyPairResourcePolicyData,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> list[SlotQuantity]:
        """Resolve a resource policy into per-slot limits."""
        limits_slot = ResourceSlot.from_policy(
            {
                "total_resource_slots": resource_policy.total_resource_slots,
                "default_for_unspecified": resource_policy.default_for_unspecified,
            },
            cast(Mapping[str, Any], known_slot_types),
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

        result = await self._sess.execute(query)
        quantities = [
            SlotQuantity(row.slot_name, row.total) for row in result if row.total is not None
        ]
        if not quantities:
            return [
                SlotQuantity(str(slot_name), Decimal(0)) for slot_name in known_slot_types.keys()
            ]
        return quantities
