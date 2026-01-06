"""Database source for audit log repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import (
    Creator,
    execute_creator,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("AuditLogDBSource",)


class AuditLogDBSource:
    """Database source for audit log operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create(self, creator: Creator[AuditLogRow]) -> AuditLogRow:
        """Creates a new audit log entry."""
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row
