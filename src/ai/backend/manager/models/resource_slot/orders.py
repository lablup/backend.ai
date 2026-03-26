"""Query orders for resource slot rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.resource_slot.types import (
    AgentResourceOrderField,
    OrderDirection,
    ResourceAllocationOrderField,
    ResourceSlotTypeOrderField,
)
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.repositories.base import QueryOrder

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]

# ========== ResourceSlotType orders ==========

SLOT_TYPE_ORDER_FIELD_MAP: dict[ResourceSlotTypeOrderField, _OrderColumn] = {
    ResourceSlotTypeOrderField.SLOT_NAME: ResourceSlotTypeRow.slot_name,
    ResourceSlotTypeOrderField.RANK: ResourceSlotTypeRow.rank,
    ResourceSlotTypeOrderField.DISPLAY_NAME: ResourceSlotTypeRow.display_name,
}

SLOT_TYPE_DEFAULT_FORWARD_ORDER: QueryOrder = ResourceSlotTypeRow.slot_name.asc()
SLOT_TYPE_DEFAULT_BACKWARD_ORDER: QueryOrder = ResourceSlotTypeRow.slot_name.desc()
SLOT_TYPE_TIEBREAKER_ORDER: QueryOrder = ResourceSlotTypeRow.slot_name.asc()


class ResourceSlotTypeOrders:
    """Order factories for resource slot type rows."""

    @staticmethod
    def slot_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceSlotTypeRow.slot_name.asc()
        return ResourceSlotTypeRow.slot_name.desc()

    @staticmethod
    def rank(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceSlotTypeRow.rank.asc()
        return ResourceSlotTypeRow.rank.desc()

    @staticmethod
    def display_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceSlotTypeRow.display_name.asc()
        return ResourceSlotTypeRow.display_name.desc()


def resolve_slot_type_order(
    field: ResourceSlotTypeOrderField, direction: OrderDirection
) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = SLOT_TYPE_ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()


# ========== AgentResource orders ==========

AGENT_RESOURCE_ORDER_FIELD_MAP: dict[AgentResourceOrderField, _OrderColumn] = {
    AgentResourceOrderField.AGENT_ID: AgentResourceRow.agent_id,
    AgentResourceOrderField.SLOT_NAME: AgentResourceRow.slot_name,
}

AGENT_RESOURCE_DEFAULT_FORWARD_ORDER: QueryOrder = AgentResourceRow.slot_name.asc()
AGENT_RESOURCE_DEFAULT_BACKWARD_ORDER: QueryOrder = AgentResourceRow.slot_name.desc()
AGENT_RESOURCE_TIEBREAKER_ORDER: QueryOrder = AgentResourceRow.slot_name.asc()


class AgentResourceOrders:
    """Order factories for agent resource rows."""

    @staticmethod
    def slot_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentResourceRow.slot_name.asc()
        return AgentResourceRow.slot_name.desc()

    @staticmethod
    def capacity(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentResourceRow.capacity.asc()
        return AgentResourceRow.capacity.desc()

    @staticmethod
    def used(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentResourceRow.used.asc()
        return AgentResourceRow.used.desc()


def resolve_agent_resource_order(
    field: AgentResourceOrderField, direction: OrderDirection
) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = AGENT_RESOURCE_ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()


# ========== ResourceAllocation orders ==========

RESOURCE_ALLOCATION_ORDER_FIELD_MAP: dict[ResourceAllocationOrderField, _OrderColumn] = {
    ResourceAllocationOrderField.KERNEL_ID: ResourceAllocationRow.kernel_id,
    ResourceAllocationOrderField.SLOT_NAME: ResourceAllocationRow.slot_name,
}

RESOURCE_ALLOCATION_DEFAULT_FORWARD_ORDER: QueryOrder = ResourceAllocationRow.slot_name.asc()
RESOURCE_ALLOCATION_DEFAULT_BACKWARD_ORDER: QueryOrder = ResourceAllocationRow.slot_name.desc()
RESOURCE_ALLOCATION_TIEBREAKER_ORDER: QueryOrder = ResourceAllocationRow.slot_name.asc()


class ResourceAllocationOrders:
    """Order factories for resource allocation rows."""

    @staticmethod
    def slot_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceAllocationRow.slot_name.asc()
        return ResourceAllocationRow.slot_name.desc()

    @staticmethod
    def requested(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceAllocationRow.requested.asc()
        return ResourceAllocationRow.requested.desc()

    @staticmethod
    def used(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceAllocationRow.used.asc()
        return ResourceAllocationRow.used.desc()


def resolve_resource_allocation_order(
    field: ResourceAllocationOrderField, direction: OrderDirection
) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = RESOURCE_ALLOCATION_ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()
