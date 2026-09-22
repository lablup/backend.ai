from typing import override

from ai.backend.common.data.entity.types import DanglingFieldType, FieldIdentifier, FieldType

__all__ = (
    "AuditLogFieldType",
    "AuditLogScopeFieldType",
    "AuditLogID",
    "AuditLogScopeID",
)


class AuditLogFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "audit_log"

    @override
    @classmethod
    def description(cls) -> str:
        return "One record of an action, naming who ran it and what it acted on."


class AuditLogScopeFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "audit_log_scope"

    @override
    @classmethod
    def description(cls) -> str:
        return (
            "The scope a scope or relation action targeted. The record itself names the"
            " entity that was touched, so only this makes a search by the scope find it."
        )


class AuditLogID(FieldIdentifier):
    """One audit record's id.

    A field of whatever entity the recorded action was about, so the owner's type is a
    value on the row rather than a declaration here — and a record of an action that
    named nothing has no owner at all.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return AuditLogFieldType()


class AuditLogScopeID(FieldIdentifier):
    """One scope an audit record sits in, owned by that record."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return AuditLogScopeFieldType()
