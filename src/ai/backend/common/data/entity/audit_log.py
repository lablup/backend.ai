from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = (
    "AUDIT_LOG_FIELD_TYPE",
    "AUDIT_LOG_SCOPE_FIELD_TYPE",
    "AuditLogID",
    "AuditLogScopeID",
)


AUDIT_LOG_FIELD_TYPE = FieldType("audit_log")
AUDIT_LOG_SCOPE_FIELD_TYPE = FieldType("audit_log_scope")


class AuditLogID(FieldIdentifier):
    """One audit record's id.

    A field of whatever entity the recorded action was about, so the owner's type is a
    value on the row rather than a declaration here — and a record of an action that
    named nothing has no owner at all.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return AUDIT_LOG_FIELD_TYPE


class AuditLogScopeID(FieldIdentifier):
    """One scope an audit record sits in, owned by that record."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return AUDIT_LOG_SCOPE_FIELD_TYPE
