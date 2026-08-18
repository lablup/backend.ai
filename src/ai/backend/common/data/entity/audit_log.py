from ai.backend.common.data.entity.types import EntityType, SidecarIdentifier

__all__ = (
    "AUDIT_LOG_ENTITY_TYPE",
    "AuditLogID",
    "AuditLogScopeID",
)


# Raw string mirroring the RBAC-managed EntityType.AUDIT_LOG value. An audit row is not
# an entity; this names the kind of thing the rows are about, on the action that reads them.
AUDIT_LOG_ENTITY_TYPE = EntityType("audit_log")


class AuditLogID(SidecarIdentifier):
    pass


class AuditLogScopeID(SidecarIdentifier):
    pass
