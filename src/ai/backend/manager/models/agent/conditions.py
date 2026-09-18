"""Query conditions for agent rows."""

from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.repositories.base import QueryCondition

from .row import AgentRow


class AgentConditions:
    """Query condition factories for filtering agent rows."""

    @staticmethod
    def by_ids(ids: Collection[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.id.in_(ids)

        return inner

    # --- id string conditions ---

    @staticmethod
    def by_id_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.id.ilike(f"%{spec.value}%")
            else:
                condition = AgentRow.id.like(f"%{spec.value}%")
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_id_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AgentRow.id) == spec.value.lower()
            else:
                condition = AgentRow.id == spec.value
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_id_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.id.ilike(f"{spec.value}%")
            else:
                condition = AgentRow.id.like(f"{spec.value}%")
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_id_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.id.ilike(f"%{spec.value}")
            else:
                condition = AgentRow.id.like(f"%{spec.value}")
            return ~condition if spec.negated else condition

        return inner

    by_id_in = staticmethod(make_string_in_factory(AgentRow.id))

    # --- status enum conditions ---

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
    def by_status_not_equals(status: AgentStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.status != status

        return inner

    @staticmethod
    def by_status_not_in(statuses: Collection[AgentStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.status.not_in(statuses)

        return inner

    # --- schedulable boolean condition ---

    @staticmethod
    def by_schedulable(schedulable: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.schedulable.is_(schedulable)

        return inner

    # --- scaling_group string conditions ---

    @staticmethod
    def by_scaling_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.scaling_group.ilike(f"%{spec.value}%")
            else:
                condition = AgentRow.scaling_group.like(f"%{spec.value}%")
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_scaling_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AgentRow.scaling_group) == spec.value.lower()
            else:
                condition = AgentRow.scaling_group == spec.value
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_scaling_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.scaling_group.ilike(f"{spec.value}%")
            else:
                condition = AgentRow.scaling_group.like(f"{spec.value}%")
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_scaling_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.scaling_group.ilike(f"%{spec.value}")
            else:
                condition = AgentRow.scaling_group.like(f"%{spec.value}")
            return ~condition if spec.negated else condition

        return inner

    by_scaling_group_in = staticmethod(make_string_in_factory(AgentRow.scaling_group))

    # --- cursor pagination conditions ---

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
