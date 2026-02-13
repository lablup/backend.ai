from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.types import AgentId
from ai.backend.manager.api.gql.base import StringMatchSpec
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
    def by_statuses(statuses: Collection[AgentStatus]) -> QueryCondition:
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
