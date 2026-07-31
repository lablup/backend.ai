"""Batch-purge spec for retention cleanup.

One spec expresses every target: rows of a table older than ``threshold`` on a
boundary timestamp. When ``match_column`` is set the boundary lives on a parent
table and the rows are matched through their foreign key -- this covers the
FK-less children of the ordered-delete categories.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class RetentionPurgerSpec[TRow: Base](BatchPurgerSpec[TRow]):
    """Selects rows older than ``threshold`` on ``boundary``.

    A NULL boundary is never selected, so a lifecycle record still lacking its
    terminal timestamp is preserved. ``conditions`` narrows the target rows
    (terminal-status / discriminator filters). When ``match_column`` is set the
    boundary belongs to a parent table: rows are kept whose ``match_column`` is
    among ``source_key`` values past the boundary (with ``source_conditions``),
    letting an FK-less child be drained by its parent.
    """

    # Any-typed columns: targets span declaratively- and imperatively-mapped
    # attributes and nullable lifecycle columns.
    row_class: type[TRow]
    boundary: Any
    threshold: datetime
    conditions: Sequence[Any] = field(default_factory=tuple)
    match_column: Any = None
    source_key: Any = None
    source_conditions: Sequence[Any] = field(default_factory=tuple)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[TRow]]:
        if self.match_column is None:
            stmt = sa.select(self.row_class).where(self.boundary < self.threshold)
        else:
            source = sa.select(self.source_key).where(self.boundary < self.threshold)
            for condition in self.source_conditions:
                source = source.where(condition)
            stmt = sa.select(self.row_class).where(self.match_column.in_(source))
        for condition in self.conditions:
            stmt = stmt.where(condition)
        return stmt

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
