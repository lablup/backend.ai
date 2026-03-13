from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

if TYPE_CHECKING:
    from ai.backend.common.data.filter_specs import StringMatchSpec


class AuditLogConditions:
    """Query conditions for audit logs."""

    @staticmethod
    def by_ids(audit_log_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AuditLogRow.id.in_(audit_log_ids)

        return inner

    # --- entity_type string filters ---

    @staticmethod
    def by_entity_type_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AuditLogRow.entity_type.ilike(f"%{spec.value}%")
            else:
                condition = AuditLogRow.entity_type.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_entity_type_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AuditLogRow.entity_type) == spec.value.lower()
            else:
                condition = AuditLogRow.entity_type == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_entity_type_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AuditLogRow.entity_type.ilike(f"{spec.value}%")
            else:
                condition = AuditLogRow.entity_type.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_entity_type_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AuditLogRow.entity_type.ilike(f"%{spec.value}")
            else:
                condition = AuditLogRow.entity_type.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # --- operation string filters ---

    @staticmethod
    def by_operation_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AuditLogRow.operation.ilike(f"%{spec.value}%")
            else:
                condition = AuditLogRow.operation.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_operation_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AuditLogRow.operation) == spec.value.lower()
            else:
                condition = AuditLogRow.operation == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_operation_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AuditLogRow.operation.ilike(f"{spec.value}%")
            else:
                condition = AuditLogRow.operation.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_operation_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AuditLogRow.operation.ilike(f"%{spec.value}")
            else:
                condition = AuditLogRow.operation.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # --- status enum filters ---

    @staticmethod
    def by_status_in(statuses: Collection[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AuditLogRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_not_in(statuses: Collection[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AuditLogRow.status.notin_(statuses)

        return inner

    # --- created_at datetime filters ---

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AuditLogRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AuditLogRow.created_at > dt

        return inner

    # --- triggered_by string filters ---

    @staticmethod
    def by_triggered_by_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AuditLogRow.triggered_by.ilike(f"%{spec.value}%")
            else:
                condition = AuditLogRow.triggered_by.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_triggered_by_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AuditLogRow.triggered_by) == spec.value.lower()
            else:
                condition = AuditLogRow.triggered_by == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_triggered_by_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AuditLogRow.triggered_by.ilike(f"{spec.value}%")
            else:
                condition = AuditLogRow.triggered_by.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_triggered_by_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AuditLogRow.triggered_by.ilike(f"%{spec.value}")
            else:
                condition = AuditLogRow.triggered_by.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # --- cursor pagination conditions ---

    @staticmethod
    def by_cursor_forward(cursor_value: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AuditLogRow.created_at < sa.func.to_timestamp(
                cursor_value, "YYYY-MM-DD HH24:MI:SS.US+TZ"
            )

        return inner

    @staticmethod
    def by_cursor_backward(cursor_value: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AuditLogRow.created_at > sa.func.to_timestamp(
                cursor_value, "YYYY-MM-DD HH24:MI:SS.US+TZ"
            )

        return inner


class AuditLogOrders:
    """Query orders for audit logs."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AuditLogRow.created_at.asc()
        return AuditLogRow.created_at.desc()

    @staticmethod
    def entity_type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AuditLogRow.entity_type.asc()
        return AuditLogRow.entity_type.desc()

    @staticmethod
    def operation(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AuditLogRow.operation.asc()
        return AuditLogRow.operation.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AuditLogRow.status.asc()
        return AuditLogRow.status.desc()
