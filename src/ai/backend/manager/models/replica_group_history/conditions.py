"""Query conditions for replica group history rows."""

from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import ReplicaGroupHandlerCategory
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow


class ReplicaGroupHistoryConditions:
    """Query conditions for replica group history."""

    # UUID filter conditions for history id
    @staticmethod
    def by_id_filter(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return ReplicaGroupHistoryRow.id != spec.value
            return ReplicaGroupHistoryRow.id == spec.value

        return inner

    @staticmethod
    def by_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return ReplicaGroupHistoryRow.id.notin_(spec.values)
            return ReplicaGroupHistoryRow.id.in_(spec.values)

        return inner

    @staticmethod
    def by_replica_group_id(replica_group_id: ReplicaGroupID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.replica_group_id == replica_group_id

        return inner

    @staticmethod
    def by_replica_group_ids(group_ids: Collection[ReplicaGroupID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.replica_group_id.in_(group_ids)

        return inner

    @staticmethod
    def by_category(category: ReplicaGroupHandlerCategory) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.category == category

        return inner

    @staticmethod
    def by_categories(categories: list[ReplicaGroupHandlerCategory]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.category.in_(categories)

        return inner

    @staticmethod
    def by_result(result: SchedulingResult) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.result == str(result)

        return inner

    @staticmethod
    def by_results(results: list[SchedulingResult]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.result.in_([str(r) for r in results])

        return inner

    @staticmethod
    def by_result_not_equals(result: SchedulingResult) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.result != str(result)

        return inner

    @staticmethod
    def by_result_not_in(results: list[SchedulingResult]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.result.not_in([str(r) for r in results])

        return inner

    @staticmethod
    def by_from_statuses(statuses: list[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.from_status.in_(statuses)

        return inner

    @staticmethod
    def by_to_statuses(statuses: list[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.to_status.in_(statuses)

        return inner

    # String filter conditions for error_code
    @staticmethod
    def by_error_code_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ReplicaGroupHistoryRow.error_code.ilike(f"%{spec.value}%")
            else:
                condition = ReplicaGroupHistoryRow.error_code.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_error_code_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ReplicaGroupHistoryRow.error_code) == spec.value.lower()
            else:
                condition = ReplicaGroupHistoryRow.error_code == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_error_code_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ReplicaGroupHistoryRow.error_code.ilike(f"{spec.value}%")
            else:
                condition = ReplicaGroupHistoryRow.error_code.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_error_code_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ReplicaGroupHistoryRow.error_code.ilike(f"%{spec.value}")
            else:
                condition = ReplicaGroupHistoryRow.error_code.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # String filter conditions for phase
    @staticmethod
    def by_phase_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ReplicaGroupHistoryRow.phase.ilike(f"%{spec.value}%")
            else:
                condition = ReplicaGroupHistoryRow.phase.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_phase_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ReplicaGroupHistoryRow.phase) == spec.value.lower()
            else:
                condition = ReplicaGroupHistoryRow.phase == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_phase_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ReplicaGroupHistoryRow.phase.ilike(f"{spec.value}%")
            else:
                condition = ReplicaGroupHistoryRow.phase.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_phase_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ReplicaGroupHistoryRow.phase.ilike(f"%{spec.value}")
            else:
                condition = ReplicaGroupHistoryRow.phase.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # String filter conditions for message
    @staticmethod
    def by_message_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ReplicaGroupHistoryRow.message.ilike(f"%{spec.value}%")
            else:
                condition = ReplicaGroupHistoryRow.message.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_message_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ReplicaGroupHistoryRow.message) == spec.value.lower()
            else:
                condition = ReplicaGroupHistoryRow.message == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_message_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ReplicaGroupHistoryRow.message.ilike(f"{spec.value}%")
            else:
                condition = ReplicaGroupHistoryRow.message.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_message_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ReplicaGroupHistoryRow.message.ilike(f"%{spec.value}")
            else:
                condition = ReplicaGroupHistoryRow.message.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_phase_in = staticmethod(make_string_in_factory(ReplicaGroupHistoryRow.phase))
    by_error_code_in = staticmethod(make_string_in_factory(ReplicaGroupHistoryRow.error_code))
    by_message_in = staticmethod(make_string_in_factory(ReplicaGroupHistoryRow.message))

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ReplicaGroupHistoryRow.created_at)
                .where(ReplicaGroupHistoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return ReplicaGroupHistoryRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ReplicaGroupHistoryRow.created_at)
                .where(ReplicaGroupHistoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return ReplicaGroupHistoryRow.created_at > subquery

        return inner

    # DateTime filter conditions
    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.created_at == dt

        return inner

    @staticmethod
    def by_updated_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.updated_at < dt

        return inner

    @staticmethod
    def by_updated_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.updated_at > dt

        return inner

    @staticmethod
    def by_updated_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.updated_at == dt

        return inner
