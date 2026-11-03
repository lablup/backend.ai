"""Session writes that only the session db source runs.

Renaming a session also renames its kernels, and the caller reads the row back with
its kernels, so the primitives sit here on top of the general v2 write ops.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps

__all__ = ("V2SessionWriteOps",)


class V2SessionWriteOps(V2WriteOps):
    """The general v2 write ops plus the session rows a rename reads and writes."""

    async def session_row(self, session_id: SessionID) -> SessionRow | None:
        """Read the session row, without its kernels."""
        row: SessionRow | None = await self._sess.scalar(
            sa.select(SessionRow).where(SessionRow.id == session_id)
        )
        return row

    async def rename_kernels(self, session_id: SessionID, session_name: str) -> None:
        """Copy the session's new name onto every kernel of the session."""
        await self._sess.execute(
            sa.update(KernelRow)
            .values(session_name=session_name)
            .where(KernelRow.session_id == session_id)
        )

    async def session_row_with_kernels(self, session_id: SessionID) -> SessionRow | None:
        """Read the session row again with its kernels loaded."""
        row: SessionRow | None = await self._sess.scalar(
            sa.select(SessionRow)
            .options(selectinload(SessionRow.kernels))
            .execution_options(populate_existing=True)
            .where(SessionRow.id == session_id)
        )
        return row
