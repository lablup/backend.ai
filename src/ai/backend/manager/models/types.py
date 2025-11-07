from typing import TYPE_CHECKING

import sqlalchemy as sa

if TYPE_CHECKING:
    from ai.backend.manager.repositories.types import QueryOptionCallable


def load_related_field(field: sa.orm.Load) -> "QueryOptionCallable":
    return lambda stmt: stmt.options(field)


def join_by_related_field(field: sa.orm.attributes.InstrumentedAttribute) -> "QueryOptionCallable":
    return lambda stmt: stmt.join(field)
