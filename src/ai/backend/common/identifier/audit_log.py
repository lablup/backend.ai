from typing import NewType
from uuid import UUID

__all__ = ("AuditLogID",)


AuditLogID = NewType("AuditLogID", UUID)
