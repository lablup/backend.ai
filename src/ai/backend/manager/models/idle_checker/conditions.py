from __future__ import annotations

from collections.abc import Collection
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.data.idle_checker.types import CheckerType, IdleCheckPhase
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import make_string_in_factory

from .row import IdleCheckerBindingRow, IdleCheckerRow, SessionIdleCheckRow


class IdleCheckerConditions:
    by_name_in = staticmethod(make_string_in_factory(IdleCheckerRow.name))

    @staticmethod
    def by_ids(checker_ids: Collection[IdleCheckerID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerRow.id.in_(checker_ids)

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = IdleCheckerRow.name.ilike(f"%{spec.value}%")
            else:
                condition = IdleCheckerRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(IdleCheckerRow.name) == spec.value.lower()
            else:
                condition = IdleCheckerRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = IdleCheckerRow.name.ilike(f"{spec.value}%")
            else:
                condition = IdleCheckerRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = IdleCheckerRow.name.ilike(f"%{spec.value}")
            else:
                condition = IdleCheckerRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_checker_type_equals(checker_type: CheckerType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerRow.checker_type == checker_type

        return inner

    @staticmethod
    def by_checker_type_in(checker_types: Collection[CheckerType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerRow.checker_type.in_(checker_types)

        return inner

    @staticmethod
    def by_created_at_before(value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerRow.created_at < value

        return inner

    @staticmethod
    def by_created_at_after(value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerRow.created_at > value

        return inner

    @staticmethod
    def by_created_at_equals(value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerRow.created_at == value

        return inner

    @staticmethod
    def by_updated_at_before(value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerRow.updated_at < value

        return inner

    @staticmethod
    def by_updated_at_after(value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerRow.updated_at > value

        return inner

    @staticmethod
    def by_updated_at_equals(value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerRow.updated_at == value

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        cursor_uuid = IdleCheckerID(UUID(cursor_id))

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            cursor_created_at = (
                sa.select(IdleCheckerRow.created_at)
                .where(IdleCheckerRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return IdleCheckerRow.created_at < cursor_created_at

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        cursor_uuid = IdleCheckerID(UUID(cursor_id))

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            cursor_created_at = (
                sa.select(IdleCheckerRow.created_at)
                .where(IdleCheckerRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return IdleCheckerRow.created_at > cursor_created_at

        return inner


class IdleCheckerBindingConditions:
    @staticmethod
    def enabled() -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerBindingRow.enabled == sa.true()

        return inner


class SessionIdleCheckConditions:
    @staticmethod
    def by_pairs(
        pairs: Collection[tuple[SessionId, IdleCheckerID]],
    ) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.tuple_(
                SessionIdleCheckRow.session_id,
                SessionIdleCheckRow.idle_checker_id,
            ).in_(pairs)

        return inner

    @staticmethod
    def by_status_equals(status: IdleCheckPhase) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionIdleCheckRow.last_status == status

        return inner

    @staticmethod
    def by_status_not_equals(status: IdleCheckPhase) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionIdleCheckRow.last_status != status

        return inner
