"""Query conditions for resource slot rows."""

from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.repositories.base import QueryCondition


class ResourceSlotTypeConditions:
    """Query condition factories for filtering resource slot type rows."""

    @staticmethod
    def by_slot_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceSlotTypeRow.slot_name.ilike(f"%{spec.value}%")
            else:
                condition = ResourceSlotTypeRow.slot_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ResourceSlotTypeRow.slot_name) == spec.value.lower()
            else:
                condition = ResourceSlotTypeRow.slot_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceSlotTypeRow.slot_name.ilike(f"{spec.value}%")
            else:
                condition = ResourceSlotTypeRow.slot_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceSlotTypeRow.slot_name.ilike(f"%{spec.value}")
            else:
                condition = ResourceSlotTypeRow.slot_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_type_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceSlotTypeRow.slot_type.ilike(f"%{spec.value}%")
            else:
                condition = ResourceSlotTypeRow.slot_type.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_type_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ResourceSlotTypeRow.slot_type) == spec.value.lower()
            else:
                condition = ResourceSlotTypeRow.slot_type == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_type_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceSlotTypeRow.slot_type.ilike(f"{spec.value}%")
            else:
                condition = ResourceSlotTypeRow.slot_type.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_type_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceSlotTypeRow.slot_type.ilike(f"%{spec.value}")
            else:
                condition = ResourceSlotTypeRow.slot_type.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_display_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceSlotTypeRow.display_name.ilike(f"%{spec.value}%")
            else:
                condition = ResourceSlotTypeRow.display_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_display_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ResourceSlotTypeRow.display_name) == spec.value.lower()
            else:
                condition = ResourceSlotTypeRow.display_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_display_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceSlotTypeRow.display_name.ilike(f"{spec.value}%")
            else:
                condition = ResourceSlotTypeRow.display_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_display_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceSlotTypeRow.display_name.ilike(f"%{spec.value}")
            else:
                condition = ResourceSlotTypeRow.display_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_slot_name: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor). slot_name is the primary key."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceSlotTypeRow.slot_name > cursor_slot_name

        return inner

    @staticmethod
    def by_cursor_backward(cursor_slot_name: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor). slot_name is the primary key."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceSlotTypeRow.slot_name < cursor_slot_name

        return inner


class AgentResourceConditions:
    """Query condition factories for filtering agent resource rows."""

    @staticmethod
    def by_agent_id(agent_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentResourceRow.agent_id == agent_id

        return inner

    @staticmethod
    def by_agent_id_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentResourceRow.agent_id.ilike(f"%{spec.value}%")
            else:
                condition = AgentResourceRow.agent_id.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_agent_id_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AgentResourceRow.agent_id) == spec.value.lower()
            else:
                condition = AgentResourceRow.agent_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_agent_id_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentResourceRow.agent_id.ilike(f"{spec.value}%")
            else:
                condition = AgentResourceRow.agent_id.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_agent_id_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentResourceRow.agent_id.ilike(f"%{spec.value}")
            else:
                condition = AgentResourceRow.agent_id.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentResourceRow.slot_name.ilike(f"%{spec.value}%")
            else:
                condition = AgentResourceRow.slot_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AgentResourceRow.slot_name) == spec.value.lower()
            else:
                condition = AgentResourceRow.slot_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentResourceRow.slot_name.ilike(f"{spec.value}%")
            else:
                condition = AgentResourceRow.slot_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentResourceRow.slot_name.ilike(f"%{spec.value}")
            else:
                condition = AgentResourceRow.slot_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_slot_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentResourceRow.slot_name > cursor_slot_name

        return inner

    @staticmethod
    def by_cursor_backward(cursor_slot_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentResourceRow.slot_name < cursor_slot_name

        return inner


class ResourceAllocationConditions:
    """Query condition factories for filtering resource allocation rows."""

    @staticmethod
    def by_kernel_id(kernel_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceAllocationRow.kernel_id == kernel_id

        return inner

    @staticmethod
    def by_slot_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceAllocationRow.slot_name.ilike(f"%{spec.value}%")
            else:
                condition = ResourceAllocationRow.slot_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ResourceAllocationRow.slot_name) == spec.value.lower()
            else:
                condition = ResourceAllocationRow.slot_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceAllocationRow.slot_name.ilike(f"{spec.value}%")
            else:
                condition = ResourceAllocationRow.slot_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_slot_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceAllocationRow.slot_name.ilike(f"%{spec.value}")
            else:
                condition = ResourceAllocationRow.slot_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_slot_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceAllocationRow.slot_name > cursor_slot_name

        return inner

    @staticmethod
    def by_cursor_backward(cursor_slot_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceAllocationRow.slot_name < cursor_slot_name

        return inner

    @staticmethod
    def by_kernel_id_filter_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return ResourceAllocationRow.kernel_id != spec.value
            return ResourceAllocationRow.kernel_id == spec.value

        return inner

    @staticmethod
    def by_kernel_id_filter_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return ResourceAllocationRow.kernel_id.not_in(spec.values)
            return ResourceAllocationRow.kernel_id.in_(spec.values)

        return inner
