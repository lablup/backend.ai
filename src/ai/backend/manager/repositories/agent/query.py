from collections.abc import Collection
from typing import Callable, Optional

import sqlalchemy as sa

from ai.backend.common.types import AgentId
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent import AgentRow

type QueryConditionCallable = Callable[
    [Optional[sa.sql.expression.BinaryExpression]], sa.sql.expression.BinaryExpression
]
type QueryCondition = Callable[[sa.sql.Select], QueryConditionCallable]

type QueryOrder = sa.sql.ClauseElement


class QueryConditions:
    @staticmethod
    def by_ids(agent_ids: Collection[AgentId]) -> QueryCondition:
        def inner(stmt: sa.sql.Select) -> sa.sql.Select:
            cond = AgentRow.id.in_(agent_ids)
            return stmt.where(cond)

        return inner

    @staticmethod
    def by_scaling_group(scaling_group: str) -> QueryCondition:
        def inner(stmt: sa.sql.Select) -> sa.sql.Select:
            cond = AgentRow.scaling_group == scaling_group
            return stmt.where(cond)

        return inner

    @staticmethod
    def by_statuses(statuses: Collection[AgentStatus]) -> QueryCondition:
        def inner(stmt: sa.sql.Select) -> sa.sql.Select:
            cond = AgentRow.status.in_(statuses)
            return stmt.where(cond)

        return inner


class QueryOrders:
    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.id.asc()
        else:
            return AgentRow.id.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.status.asc()
        else:
            return AgentRow.status.desc()

    @staticmethod
    def scaling_group(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.scaling_group.asc()
        else:
            return AgentRow.scaling_group.desc()
