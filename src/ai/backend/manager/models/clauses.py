"""Shared query-expression type aliases for the models (DB) layer.

These are plain SQLAlchemy type aliases used to build query conditions and
orderings. They live at the models layer so that entity ``conditions``/``orders``
modules do not have to import from the repositories layer (which sits above
models in the declared layer order).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import sqlalchemy as sa

# QueryCondition returns a ColumnElement (whereclause) instead of modifying stmt
type QueryCondition = Callable[[], sa.sql.expression.ColumnElement[bool]]

type QueryOrder = sa.sql.expression.UnaryExpression[Any] | sa.sql.expression.ColumnElement[Any]
