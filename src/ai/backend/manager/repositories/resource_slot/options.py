"""Query conditions and orders for Resource Slot repository."""

from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceAllocationRow
from ai.backend.manager.repositories.base.types import QueryCondition, QueryOrder


class AgentResourceConditions:
    @staticmethod
    def by_agent_id(agent_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentResourceRow.agent_id == agent_id

        return inner

    @staticmethod
    def by_slot_name(slot_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentResourceRow.slot_name == slot_name

        return inner


class AgentResourceOrders:
    @staticmethod
    def by_agent_id(ascending: bool = True) -> QueryOrder:
        col = AgentResourceRow.agent_id
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_slot_name(ascending: bool = True) -> QueryOrder:
        col = AgentResourceRow.slot_name
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_capacity(ascending: bool = True) -> QueryOrder:
        col = AgentResourceRow.capacity
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_used(ascending: bool = True) -> QueryOrder:
        col = AgentResourceRow.used
        return col.asc() if ascending else col.desc()


class ResourceAllocationConditions:
    @staticmethod
    def by_kernel_id(kernel_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceAllocationRow.kernel_id == kernel_id

        return inner

    @staticmethod
    def by_slot_name(slot_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceAllocationRow.slot_name == slot_name

        return inner


class ResourceAllocationOrders:
    @staticmethod
    def by_kernel_id(ascending: bool = True) -> QueryOrder:
        col = ResourceAllocationRow.kernel_id
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_slot_name(ascending: bool = True) -> QueryOrder:
        col = ResourceAllocationRow.slot_name
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_requested(ascending: bool = True) -> QueryOrder:
        col = ResourceAllocationRow.requested
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_used(ascending: bool = True) -> QueryOrder:
        col = ResourceAllocationRow.used
        return col.asc() if ascending else col.desc()
