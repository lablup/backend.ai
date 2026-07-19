"""Batch-purge specs for retention cleanup.

A single :class:`TimestampBoundaryPurgerSpec` covers every retention target:
common-column groups (``logs`` on ``created_at``, ``reconcile_history`` on
``updated_at``) reuse one instance per table, simple categories reuse it
directly, and lifecycle categories add a terminal-state filter through
``extra_conditions``. Keeping the boundary logic in one spec is the shared
"mixin" the design calls for — the ``category -> specs`` mapping lives in the
DB source, not here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.sql.elements import ColumnElement

from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec


@dataclass
class TimestampBoundaryPurgerSpec[TRow: Base](BatchPurgerSpec[TRow]):
    """Selects rows older than ``threshold`` on a single boundary timestamp.

    Rows whose ``boundary`` column is NULL are never selected, so a lifecycle
    record still lacking its terminal timestamp is preserved. ``extra_conditions``
    appends terminal-status / lifecycle filters (e.g. ``status == DELETED``).
    """

    row_class: type[TRow]
    # A mapped timestamp column expression. Any-typed because targets range over
    # declaratively-mapped attributes and imperatively-mapped ones (error_logs),
    # and over both non-null and nullable lifecycle columns.
    boundary: Any
    threshold: datetime
    extra_conditions: Sequence[ColumnElement[bool]] = field(default_factory=tuple)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[TRow]]:
        stmt = sa.select(self.row_class).where(self.boundary < self.threshold)
        for condition in self.extra_conditions:
            stmt = stmt.where(condition)
        return stmt
