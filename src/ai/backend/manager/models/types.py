from dataclasses import dataclass
from typing import Callable, Optional, Protocol, Self

import sqlalchemy as sa

from .exceptions import EmptySQLCondition

type QuerySingleCondition = sa.sql.expression.BinaryExpression

type QueryOptionCallable = Callable[[sa.sql.Select], sa.sql.Select]
type QueryOption = Callable[..., Callable[[sa.sql.Select], sa.sql.Select]]


@dataclass
class QueryCondition:
    """
    A class representing a SQL condition for querying.
    Raises an EmptySQLCondition exception if the condition is empty.
    """

    _sql_condition: Optional[QuerySingleCondition]

    @classmethod
    def multiple(cls, operator: Callable, conditions: list[Self]) -> Self:
        """
        Args:
            operator: The SQL operator to use for combining conditions, one of `sqlalchemy.or_`, `sqlalchemy.and_`.
            conditions: A list of QueryCondition instances to combine.
        Returns:
            A new QueryCondition instance with the combined conditions.
        """
        sql_conditions = []
        for cond in conditions:
            try:
                sql_conditions.append(cond.final_sql_condition)
            except EmptySQLCondition:
                continue
        if not sql_conditions:
            return cls(None)
        if len(sql_conditions) == 1:
            return cls(sql_conditions[0])
        return cls(operator(*sql_conditions))

    @classmethod
    def single(cls, condition: QuerySingleCondition) -> Self:
        return cls(condition)

    @property
    def final_sql_condition(self) -> QuerySingleCondition:
        if self._sql_condition is None:
            raise EmptySQLCondition
        return self._sql_condition


class _LoadableField(Protocol):
    def __call__(self, *args, **kwargs) -> Callable:
        pass


class _JoinableField(Protocol):
    def __call__(self, *args, **kwargs) -> sa.orm.attributes.InstrumentedAttribute:
        pass


def load_related_field(field: _LoadableField) -> QueryOptionCallable:
    return lambda stmt: stmt.options(field())


def join_by_related_field(field: _JoinableField) -> QueryOptionCallable:
    return lambda stmt: stmt.join(field())
