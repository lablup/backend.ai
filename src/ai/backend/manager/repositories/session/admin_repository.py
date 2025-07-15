from typing import Optional

import sqlalchemy as sa

from ai.backend.common.types import SessionId
from ai.backend.manager.models.session import (
    KernelLoadingStrategy,
    SessionRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class AdminSessionRepository:
    """
    Repository for admin-specific session operations that bypass ownership checks.
    This should only be used by superadmin users.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_session_force(
        self,
        session_id: SessionId,
        kernel_loading_strategy: KernelLoadingStrategy = KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        allow_stale: bool = False,
        eager_loading_op: Optional[list] = None,
    ) -> SessionRow:
        """Get session without ownership validation (superadmin only)"""
        async with self._db.begin_readonly_session() as db_sess:
            query_stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
            if eager_loading_op:
                for op in eager_loading_op:
                    query_stmt = query_stmt.options(op)

            session_row = await db_sess.scalar(query_stmt)
            if session_row is None:
                raise ValueError(f"Session not found (id:{session_id})")

            return session_row

    async def get_session_to_determine_status_force(
        self,
        session_id: SessionId,
    ) -> SessionRow:
        """Get session for status determination without ownership checks"""
        async with self._db.begin_readonly_session() as db_sess:
            query_stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
            session_row = await db_sess.scalar(query_stmt)
            if session_row is None:
                raise ValueError(f"Session not found (id:{session_id})")
            return session_row
