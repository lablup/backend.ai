"""Type definitions for repository layer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, TypeVar

import sqlalchemy as sa

if TYPE_CHECKING:
    from sqlalchemy.engine import Row

# QueryCondition now returns a ColumnElement (whereclause) instead of modifying stmt
type QueryCondition = Callable[[], sa.sql.expression.ColumnElement[bool]]

type QueryOrder = sa.sql.ClauseElement

# Factory function that creates a cursor condition from a decoded cursor value (str or UUID)
type CursorConditionFactory = Callable[[str], QueryCondition]

TRow = TypeVar("TRow", bound="Row")
