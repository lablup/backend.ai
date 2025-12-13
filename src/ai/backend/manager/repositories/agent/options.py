from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class AgentConditions:
    @staticmethod
    def by_id_contains(id: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return AgentRow.id.ilike(f"%{id}%")
            else:
                return AgentRow.id.like(f"%{id}%")

        return inner

    @staticmethod
    def by_id_equals(id: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(AgentRow.id) == id.lower()
            else:
                return AgentRow.id == id

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
        else:
            return AgentRow.id.desc()

    @staticmethod
    def scaling_group(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.scaling_group.asc()
        else:
            return AgentRow.scaling_group.desc()

    @staticmethod
    def first_contact(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.first_contact.asc()
        else:
            return AgentRow.first_contact.desc()

    @staticmethod
    def schedulable(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.schedulable.asc()
        else:
            return AgentRow.schedulable.desc()
