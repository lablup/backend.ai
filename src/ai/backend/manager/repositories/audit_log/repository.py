"""Repository for audit log data access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import Creator

from .db_source import AuditLogDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("AuditLogRepository",)


class AuditLogRepository:
    """Repository for audit log-related data access."""

    _db_source: AuditLogDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AuditLogDBSource(db)

    async def create(self, creator: Creator[AuditLogRow]) -> AuditLogRow:
        """Creates a new audit log entry."""
        return await self._db_source.create(creator)
