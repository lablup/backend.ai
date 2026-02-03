from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class AgentConditions:
    @staticmethod
    def by_id_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.id.ilike(f"%{spec.value}%")
            else:
                condition = AgentRow.id.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_id_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AgentRow.id) == spec.value.lower()
            else:
                condition = AgentRow.id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_id_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.id.ilike(f"{spec.value}%")
            else:
                condition = AgentRow.id.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_id_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.id.ilike(f"%{spec.value}")
            else:
                condition = AgentRow.id.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_status_contains(statuses: Collection[AgentStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_equals(status: AgentStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.status == status

        return inner

    @staticmethod
    def by_schedulable(schedulable: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.schedulable.is_(schedulable)

        return inner

    @staticmethod
    def by_scaling_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.scaling_group.ilike(f"%{spec.value}%")
            else:
                condition = AgentRow.scaling_group.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scaling_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AgentRow.scaling_group) == spec.value.lower()
            else:
                condition = AgentRow.scaling_group == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scaling_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.scaling_group.ilike(f"{spec.value}%")
            else:
                condition = AgentRow.scaling_group.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scaling_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.scaling_group.ilike(f"%{spec.value}")
            else:
                condition = AgentRow.scaling_group.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get first_contact of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(AgentRow.first_contact).where(AgentRow.id == cursor_id).scalar_subquery()
            )
            return AgentRow.first_contact < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get first_contact of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(AgentRow.first_contact).where(AgentRow.id == cursor_id).scalar_subquery()
            )
            return AgentRow.first_contact > subquery

        return inner


class AgentOrders:
    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.id.asc()
        return AgentRow.id.desc()

    @staticmethod
    def scaling_group(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.scaling_group.asc()
        return AgentRow.scaling_group.desc()

    @staticmethod
    def first_contact(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.first_contact.asc()
        return AgentRow.first_contact.desc()

    @staticmethod
    def schedulable(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.schedulable.asc()
        return AgentRow.schedulable.desc()
