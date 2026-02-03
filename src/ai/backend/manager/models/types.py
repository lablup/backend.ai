from collections.abc import Callable
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm.strategy_options import _AbstractLoad

# QueryCondition: function that takes a Select and returns a modified Select with where clause
type QueryCondition = Callable[[sa.sql.Select[Any]], sa.sql.Select[Any]]

# QueryOption: function that takes a Select and returns a modified Select with options
type QueryOption = Callable[[sa.sql.Select[Any]], sa.sql.Select[Any]]


def load_related_field(field: _AbstractLoad) -> QueryOption:
    return lambda stmt: stmt.options(field)


def join_by_related_field(field: sa.orm.attributes.InstrumentedAttribute[Any]) -> QueryOption:
    return lambda stmt: stmt.join(field)
