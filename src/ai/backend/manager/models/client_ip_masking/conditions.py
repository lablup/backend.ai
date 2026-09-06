"""Query conditions for client IP masking policy rows."""

from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow

__all__ = ("ClientIPMaskingPolicyConditions",)


class ClientIPMaskingPolicyConditions:
    @staticmethod
    def by_target_type(target_type: ClientIPMaskingTarget) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ClientIPMaskingPolicyRow.target_type == target_type

        return inner

    @staticmethod
    def by_mode(mode: ClientIPMaskingMode) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ClientIPMaskingPolicyRow.mode == mode

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination, keyed on the ordered column."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ClientIPMaskingPolicyRow.target_type)
                .where(ClientIPMaskingPolicyRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return ClientIPMaskingPolicyRow.target_type > subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination, keyed on the ordered column."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ClientIPMaskingPolicyRow.target_type)
                .where(ClientIPMaskingPolicyRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return ClientIPMaskingPolicyRow.target_type < subquery

        return inner
