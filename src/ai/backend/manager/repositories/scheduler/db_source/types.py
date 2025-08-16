"""Types for database source operations."""

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.types import SessionId
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models import SessionRow


class SessionRowCache:
    """Cache for pre-fetched session rows with lazy loading support."""

    def __init__(self, prefetched: dict[SessionId, SessionRow]):
        self._cache = prefetched

    async def get_or_fetch(self, db_sess: SASession, session_id: SessionId) -> SessionRow:
        """Get session from cache or fetch from database if not present."""
        if session_id in self._cache:
            return self._cache[session_id]

        # Fetch if not in cache
        query = sa.select(SessionRow).where(SessionRow.id == session_id)
        result = await db_sess.execute(query)
        session_row = result.scalar_one_or_none()

        if session_row is None:
            raise SessionNotFound(str(session_id))

        # Cache for future use
        self._cache[session_id] = session_row
        return session_row
