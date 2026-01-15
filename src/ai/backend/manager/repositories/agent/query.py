from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.types import AgentId
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class QueryConditions:
    @staticmethod
    def by_ids(agent_ids: Collection[AgentId]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.id.in_(agent_ids)

        return inner

    @staticmethod
    def by_scaling_group(scaling_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.scaling_group == scaling_group

        return inner

    @staticmethod
    def by_statuses(statuses: Collection[AgentStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_cursor_forward(cursor_value: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.id > cursor_value

        return inner

    @staticmethod
    def by_cursor_backward(cursor_value: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.id < cursor_value

        return inner


class QueryOrders:
    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.id.asc()
        return AgentRow.id.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.status.asc()
        return AgentRow.status.desc()

    @staticmethod
    def scaling_group(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.scaling_group.asc()
        return AgentRow.scaling_group.desc()
