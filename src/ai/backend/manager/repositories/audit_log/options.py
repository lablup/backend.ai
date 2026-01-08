from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import QueryCondition


class AuditLogConditions:
    """Query conditions for audit logs."""

    @staticmethod
    def by_ids(audit_log_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AuditLogRow.id.in_(audit_log_ids)

        return inner
