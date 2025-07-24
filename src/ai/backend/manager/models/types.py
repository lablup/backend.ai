from typing import Callable, Optional

import sqlalchemy as sa

type QueryConditionCallable = Callable[
    [Optional[sa.sql.expression.BinaryExpression]], sa.sql.expression.BinaryExpression
]
type QueryCondition = Callable[[sa.sql.Select], QueryConditionCallable]

type QueryOptionCallable = Callable[[sa.sql.Select], sa.sql.Select]
type QueryOption = Callable[..., Callable[[sa.sql.Select], sa.sql.Select]]


def load_related_field(field: sa.orm.Load) -> QueryOptionCallable:
    return lambda stmt: stmt.options(field)


def join_by_related_field(field: sa.orm.attributes.InstrumentedAttribute) -> QueryOptionCallable:
    return lambda stmt: stmt.join(field)
