from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import ReplicaGroupHandlerCategory
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.repositories.base import QueryCondition


class ReplicaGroupHistoryConditions:
    """Query conditions for replica group history."""

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
<<<<<<< HEAD
=======

    @staticmethod
    def by_categories(categories: Collection[ReplicaGroupHandlerCategory]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.category.in_(categories)

        return inner

    @staticmethod
    def by_result(result: SchedulingResult) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.result == str(result)

        return inner

    @staticmethod
    def by_results(results: Collection[SchedulingResult]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.result.in_([str(r) for r in results])

        return inner

    @staticmethod
    def by_result_not_equals(result: SchedulingResult) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.result != str(result)

        return inner

    @staticmethod
    def by_result_not_in(results: Collection[SchedulingResult]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.result.not_in([str(r) for r in results])

        return inner

    @staticmethod
    def by_from_statuses(statuses: Collection[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.from_status.in_(statuses)

        return inner

    @staticmethod
    def by_to_statuses(statuses: Collection[str]) -> QueryCondition:
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
>>>>>>> e643d3184 (fix(BA-7979): include the tiebreaker in cursor pagination conditions (#14734))
