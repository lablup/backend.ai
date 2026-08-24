"""Retention writes: draining the rows a category has aged out.

Retention deletes plain rows across every table a policy covers and answers with a
count, not with the rows -- a category can drain millions and materializing them
would be the whole tick. Nothing else has that shape, so the primitive sits here:
:class:`RetentionWriteOps` extends the general write ops, and a repository handed
the general ones never sees it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


@dataclass
class RetentionDrain[TRow: Base]:
    """Selects the rows of one table older than ``threshold`` on ``boundary``.

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


class RetentionWriteOps(V2WriteOps):
    """The general v2 write ops plus the aged-out row drain."""

    async def drain(self, spec: RetentionDrain[Any], batch_size: int) -> int:
        """Delete the spec's rows in ``batch_size`` chunks; total deleted.

        Composite primary keys are matched as a tuple, so a table keyed on more
        than one column drains the same way.
        """
        entity = spec.build_subquery().column_descriptions[0]["entity"]
        table = sa.inspect(entity).local_table
        pk_columns = list(table.primary_key.columns)

        total_deleted = 0
        while True:
            sub = spec.build_subquery().subquery()
            pk_subquery = sa.select(*[sub.c[pk.key] for pk in pk_columns]).limit(batch_size)
            stmt = sa.delete(table).where(sa.tuple_(*pk_columns).in_(pk_subquery))
            try:
                result = await self._sess.execute(stmt)
            except sa.exc.IntegrityError as e:
                raise self._parse_integrity_error(e) from e
            batch_deleted = cast(CursorResult[Any], result).rowcount
            total_deleted += batch_deleted
            if batch_deleted < batch_size:
                break
        return total_deleted
