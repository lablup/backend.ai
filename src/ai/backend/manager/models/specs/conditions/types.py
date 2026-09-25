"""Column type the per-value-type conditions take."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

type FilterColumn = InstrumentedAttribute[Any] | sa.sql.expression.ColumnElement[Any]
