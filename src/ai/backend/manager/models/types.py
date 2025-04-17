import enum
from collections.abc import Mapping
from typing import Callable, Optional, Protocol

import sqlalchemy as sa

type QueryConditionCallable = Callable[
    [Optional[sa.sql.expression.BinaryExpression]], sa.sql.expression.BinaryExpression
]
type QueryCondition = Callable[..., QueryConditionCallable]

type QueryOptionCallable = Callable[[sa.sql.Select], sa.sql.Select]
type QueryOption = Callable[..., Callable[[sa.sql.Select], sa.sql.Select]]


class ConditionMerger(enum.Enum):
    AND = "AND"
    OR = "OR"


_COND_SQL_OPERATOR_MAP: Mapping[ConditionMerger, Callable] = {
    ConditionMerger.AND: sa.and_,
    ConditionMerger.OR: sa.or_,
}


def append_condition(
    condition: Optional[sa.sql.expression.BinaryExpression],
    new_condition: sa.sql.expression.BinaryExpression,
    operator: ConditionMerger,
) -> sa.sql.expression.BinaryExpression:
    return (
        _COND_SQL_OPERATOR_MAP[operator](condition, new_condition)
        if condition is not None
        else new_condition
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
