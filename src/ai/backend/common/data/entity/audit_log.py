from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "AUDIT_LOG_ENTITY_TYPE",
    "AuditLogID",
)


# Raw string mirroring the RBAC-managed EntityType.AUDIT_LOG value.
AUDIT_LOG_ENTITY_TYPE = EntityType("audit_log")


class AuditLogID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AUDIT_LOG_ENTITY_TYPE
