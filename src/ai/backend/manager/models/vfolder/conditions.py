"""Query conditions for vfolder rows."""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa

if TYPE_CHECKING:
    from ai.backend.common.data.filter_specs import StringMatchSpec

from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
from ai.backend.manager.repositories.base import QueryCondition

from .row import VFolderRow


class VFolderConditions:
    """Query conditions for vfolders."""

    # ── name string filter factories ──

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.name.ilike(f"%{spec.value}%")
            else:
                condition = VFolderRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(VFolderRow.name) == spec.value.lower()
            else:
                condition = VFolderRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.name.ilike(f"{spec.value}%")
            else:
                condition = VFolderRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.name.ilike(f"%{spec.value}")
            else:
                condition = VFolderRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ── host string filter factories ──

    @staticmethod
    def by_host_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.host.ilike(f"%{spec.value}%")
            else:
                condition = VFolderRow.host.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_host_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(VFolderRow.host) == spec.value.lower()
            else:
                condition = VFolderRow.host == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_host_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.host.ilike(f"{spec.value}%")
            else:
                condition = VFolderRow.host.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_host_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.host.ilike(f"%{spec.value}")
            else:
                condition = VFolderRow.host.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ── boolean filter factories ──

    @staticmethod
    def by_cloneable(value: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.cloneable == value

        return inner

    # ── enum filter factories ──

    @staticmethod
    def by_status_in(statuses: Collection[VFolderOperationStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_not_in(statuses: Collection[VFolderOperationStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.status.notin_(statuses)

        return inner

    @staticmethod
    def by_usage_mode_in(modes: Collection[VFolderUsageMode]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.usage_mode.in_(modes)

        return inner

    @staticmethod
    def by_usage_mode_not_in(modes: Collection[VFolderUsageMode]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.usage_mode.notin_(modes)

        return inner

    # ── datetime filter factories ──

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.created_at == dt

        return inner

    # ── cursor pagination factories ──

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(VFolderRow.created_at).where(VFolderRow.id == cursor_id).scalar_subquery()
            )
            return VFolderRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(VFolderRow.created_at).where(VFolderRow.id == cursor_id).scalar_subquery()
            )
            return VFolderRow.created_at > subquery

        return inner
