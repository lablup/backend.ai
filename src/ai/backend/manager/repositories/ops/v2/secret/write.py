"""Secret sweep writes: replacing one stored secret in place.

A sweep reads a value, rewraps it outside the DB, then writes it back only if the
stored string is still the one it read. Nothing else has that shape, so the
primitive sits here: :class:`SecretWriteOps` extends the general write ops with it,
and a repository handed the general ones never sees it.
"""

from __future__ import annotations

from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.repositories.ops.v2.secret.read import SecretReadOps
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps
from ai.backend.manager.secret.types import SecretValue


class SecretWriteOps(V2WriteOps, SecretReadOps):
    """The general v2 write ops plus the stored-secret scan and conditional rewrite."""

    async def rewrite_keypair_secret(
        self, access_key: AccessKey, expected: SecretValue, replacement: SecretValue
    ) -> bool:
        """Replace one stored secret, reporting whether the row took the write.

        The stored value is part of the condition, so a keypair reissued between the
        read and the write keeps its new secret and the stale value is dropped. Two
        managers sweeping the same row leave one write and one no-op.
        """
        table = KeyPairRow.__table__
        stmt = (
            sa.update(table)
            .values({table.c.secret_key: replacement})
            .where(table.c.access_key == access_key)
            .where(table.c.secret_key == expected)
        )
        result = await self._sess.execute(stmt)
        return cast(CursorResult[Any], result).rowcount == 1
