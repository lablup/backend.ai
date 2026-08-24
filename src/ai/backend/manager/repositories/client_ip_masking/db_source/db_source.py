"""Database source for client IP masking policies."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class ClientIPMaskingDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def resolve_mode(self, target_type: ClientIPMaskingTarget) -> ClientIPMaskingMode:
        """The masking that applies to one target.

        The target's own row wins over the ``default`` row, and neither being present
        means the address is recorded as observed.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ClientIPMaskingPolicyRow).where(
                ClientIPMaskingPolicyRow.target_type.in_([
                    target_type,
                    ClientIPMaskingTarget.DEFAULT,
                ])
            )
            rows = (await session.execute(stmt)).scalars().all()
        modes = {row.target_type: row.mode for row in rows}
        if target_type in modes:
            return modes[target_type]
        return modes.get(ClientIPMaskingTarget.DEFAULT, ClientIPMaskingMode.NONE)
