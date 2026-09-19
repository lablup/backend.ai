from __future__ import annotations

import enum
from collections.abc import Callable
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


class ItemStatus(enum.StrEnum):
    ACTIVE = "active"
    DELETED = "deleted"


@pytest.fixture
def item_status_type() -> type[ItemStatus]:
    return ItemStatus


@pytest.fixture
def items_table() -> sa.Table:
    return sa.Table(
        "items",
        sa.MetaData(),
        sa.Column("id", sa.Uuid),
        sa.Column("name", sa.String),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("count", sa.Integer),
        sa.Column("status", sa.Enum(ItemStatus)),
        sa.Column("flag", sa.Boolean),
    )


@pytest.fixture
def tags_table() -> sa.Table:
    """Rows several of which point at one ``items`` row."""
    return sa.Table(
        "tags",
        sa.MetaData(),
        sa.Column("item_id", sa.Uuid),
        sa.Column("key", sa.String),
    )


@pytest.fixture
def render() -> Callable[[sa.sql.ClauseElement], str]:
    """Render an expression as PostgreSQL SQL with its values inlined, whitespace collapsed."""

    def _render(expression: sa.sql.ClauseElement) -> str:
        dialect_class: Any = postgresql.dialect
        compiled = expression.compile(
            dialect=dialect_class(), compile_kwargs={"literal_binds": True}
        )
        return " ".join(str(compiled).split())

    return _render
