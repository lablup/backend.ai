from typing import Callable, Optional, Protocol

import sqlalchemy as sa

type QueryConditionCallable = Callable[
    [Optional[sa.sql.expression.BinaryExpression]], sa.sql.expression.BinaryExpression
]
type QueryCondition = Callable[..., QueryConditionCallable]

type QueryOptionCallable = Callable[[sa.sql.Select], sa.sql.Select]
type QueryOption = Callable[..., Callable[[sa.sql.Select], sa.sql.Select]]


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
