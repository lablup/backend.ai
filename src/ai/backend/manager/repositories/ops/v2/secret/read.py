"""Secret column reads: the stored secrets of one encrypted column, in key order.

A re-encryption pass and a status query both walk a column in chunks, so the scan sits
on the read side and the write ops inherit it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa

from ai.backend.manager.errors.secret import SecretEncryptionMisconfigured
from ai.backend.manager.models.base import Base, SecretColumn
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.secret.types import SecretValue


@dataclass(frozen=True)
class SecretTarget:
    """One encrypted column, named by the row class and the two column names a pass needs.

    ``key_column`` orders the walk and addresses one row, so it must be the primary key.
    """

    row_class: type[Base]
    key_column: str
    secret_column: str

    def table(self) -> sa.Table:
        return self.row_class.__table__

    def context(self) -> str:
        """The associated data the column binds, which also names the column in a report.

        Reading it off the column type is what keeps a catalog entry from naming a column
        that holds no secret.
        """
        column_type = self.table().c[self.secret_column].type
        if not isinstance(column_type, SecretColumn):
            raise SecretEncryptionMisconfigured(
                f"{self.row_class.__name__}.{self.secret_column} is not a secret column."
            )
        return column_type.context


@dataclass(frozen=True)
class StoredSecret:
    """One row's stored secret, as a pass reads it."""

    key: Any
    value: SecretValue


class SecretReadOps(V2ReadOps):
    """The general v2 read ops plus the stored-secret scan."""

    async def scan_secrets(
        self, target: SecretTarget, after: Any | None, limit: int
    ) -> Sequence[StoredSecret]:
        """Read up to ``limit`` stored secrets past ``after``, in key order."""
        table = target.table()
        key_column = table.c[target.key_column]
        stmt = (
            sa.select(key_column, table.c[target.secret_column])
            .order_by(key_column.asc())
            .limit(limit)
        )
        if after is not None:
            stmt = stmt.where(key_column > after)
        result = await self._sess.execute(stmt)
        return [StoredSecret(key=row[0], value=row[1]) for row in result]
