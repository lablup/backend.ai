from typing import NewType
from uuid import UUID

from ai.backend.common.data.entity.types import EntityType

__all__ = (
    "AUDIT_LOG_ENTITY_TYPE",
    "AuditLogID",
)


# Raw string mirroring the RBAC-managed EntityType.AUDIT_LOG value.
AUDIT_LOG_ENTITY_TYPE = EntityType("audit_log")

AuditLogID = NewType("AuditLogID", UUID)
