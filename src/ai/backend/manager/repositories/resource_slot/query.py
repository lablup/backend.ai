from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class QueryConditions:
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


class QueryOrders:
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


class CursorConditions:
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


class AgentResourceQueryConditions:
    @staticmethod
    def by_agent_id(agent_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentResourceRow.agent_id == agent_id

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


class AgentResourceQueryOrders:
    @staticmethod
    def slot_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentResourceRow.slot_name.asc()
        return AgentResourceRow.slot_name.desc()


class ResourceAllocationQueryConditions:
    @staticmethod
    def by_kernel_id(kernel_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceAllocationRow.kernel_id == kernel_id

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


class ResourceAllocationQueryOrders:
    @staticmethod
    def slot_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceAllocationRow.slot_name.asc()
        return ResourceAllocationRow.slot_name.desc()
