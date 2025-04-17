import enum
from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol

import sqlalchemy as sa

type QueryConditionCallable = Callable[
    [Optional[sa.sql.expression.BinaryExpression]], sa.sql.expression.BinaryExpression
]
type QueryCondition = Callable[..., QueryConditionCallable]

type QueryOptionCallable = Callable[[sa.sql.Select], sa.sql.Select]
type QueryOption = Callable[..., Callable[[sa.sql.Select], sa.sql.Select]]


@dataclass
class QueryArgument:
    conditions: list[QueryCondition]
    options: list[QueryOption] = field(default_factory=list)


class ConditionMerger(enum.Enum):
    AND = "AND"
    OR = "OR"

    @property
    def sql_operator(self) -> Callable:
        match self:
            case ConditionMerger.AND:
                return sa.and_
            case ConditionMerger.OR:
                return sa.or_


def append_condition(
    condition: Optional[sa.sql.expression.BinaryExpression],
    new_condition: sa.sql.expression.BinaryExpression,
    operator: ConditionMerger,
) -> sa.sql.expression.BinaryExpression:
    return (
        operator.sql_operator(condition, new_condition) if condition is not None else new_condition
    )


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
