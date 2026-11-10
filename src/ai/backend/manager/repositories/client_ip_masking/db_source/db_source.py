"""Database source for client IP masking policies."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.data.client_ip.masking import (
    ClientIPMasker,
    ClientIPMaskingMode,
    ClientIPMaskingTarget,
)
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class ClientIPMaskingDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def resolve_masker(self, target_type: ClientIPMaskingTarget) -> ClientIPMasker:
        """The masking that applies to one target.

        The row is the unit: the target's own row wins over the ``default`` row whole,
        prefixes included. Neither being present means the address is recorded as
        observed.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ClientIPMaskingPolicyRow).where(
                ClientIPMaskingPolicyRow.target_type.in_([
                    target_type,
                    ClientIPMaskingTarget.DEFAULT,
                ])
            )
            rows = (await session.execute(stmt)).scalars().all()
        by_target = {row.target_type: row for row in rows}
        row = by_target.get(target_type) or by_target.get(ClientIPMaskingTarget.DEFAULT)
        if row is None:
            return ClientIPMasker(ClientIPMaskingMode.NONE)
        return self._to_masker(row)

    def _to_masker(self, row: ClientIPMaskingPolicyRow) -> ClientIPMasker:
        """A NULL prefix takes the built-in width."""
        defaults = ClientIPMasker(row.mode)
        return ClientIPMasker(
            mode=row.mode,
            ipv4_prefix=row.ipv4_prefix if row.ipv4_prefix is not None else defaults.ipv4_prefix,
            ipv6_prefix=row.ipv6_prefix if row.ipv6_prefix is not None else defaults.ipv6_prefix,
        )
