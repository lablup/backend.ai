"""Secret column writes: replacing one stored secret in place.

A pass reads a value, encrypts it again outside the DB, then writes it back only if the
stored string is still the one it read. Nothing else has that shape, so the primitive
sits here: :class:`SecretWriteOps` extends the general write ops with it, and a
repository handed the general ones never sees it.
"""

from __future__ import annotations

from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.manager.repositories.ops.v2.secret.read import SecretReadOps, SecretTarget
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps
from ai.backend.manager.secret.types import SecretValue


class SecretWriteOps(V2WriteOps, SecretReadOps):
    """The general v2 write ops plus the stored-secret scan and conditional rewrite."""

    async def rewrite_secret(
        self, target: SecretTarget, key: Any, expected: SecretValue, replacement: SecretValue
    ) -> bool:
        """Replace one stored secret, reporting whether the row took the write.

        The stored value is part of the condition, so a secret rewritten between the read
        and the write keeps its new value and the stale one is dropped. Two managers
        passing over the same row leave one write and one no-op.
        """
        table = target.table()
        secret_column = table.c[target.secret_column]
        stmt = (
            sa.update(table)
            .values({secret_column: replacement})
            .where(table.c[target.key_column] == key)
            .where(secret_column == expected)
        )
        result = await self._sess.execute(stmt)
        return cast(CursorResult[Any], result).rowcount == 1
