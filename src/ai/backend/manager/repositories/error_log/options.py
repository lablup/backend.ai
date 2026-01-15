from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.repositories.base import QueryCondition


class ErrorLogConditions:
    """Query conditions for error logs."""

    @staticmethod
    def by_ids(error_log_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ErrorLogRow.id.in_(error_log_ids)

        return inner
