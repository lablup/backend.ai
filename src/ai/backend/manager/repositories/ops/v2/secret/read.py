"""Secret sweep reads: the stored secrets of a column, in key order.

A sweep and a status query both walk the column in chunks, so the scan sits on the
read side and the write ops inherit it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import sqlalchemy as sa

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.secret.types import SecretValue


@dataclass(frozen=True)
class StoredKeypairSecret:
    """One keypair's stored secret, as a sweep reads it."""

    access_key: AccessKey
    value: SecretValue


class SecretReadOps(V2ReadOps):
    """The general v2 read ops plus the stored-secret scan."""

    async def scan_keypair_secrets(
        self, after: AccessKey | None, limit: int
    ) -> Sequence[StoredKeypairSecret]:
        """Read up to ``limit`` stored secrets past ``after``, in access key order.

        The order is the primary key, so a pass resumes from the last key it read.
        """
        table = KeyPairRow.__table__
        stmt = (
            sa.select(table.c.access_key, table.c.secret_key)
            .order_by(table.c.access_key.asc())
            .limit(limit)
        )
        if after is not None:
            stmt = stmt.where(table.c.access_key > after)
        result = await self._sess.execute(stmt)
        return [
            StoredKeypairSecret(access_key=AccessKey(row.access_key), value=row.secret_key)
            for row in result
        ]
