"""Read specs for error logs."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy import Row

from ai.backend.common.data.entity.error_log import ErrorLogID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class ErrorLogOwnerLookup(FieldOwnerLookup[ErrorLogID, UserID]):
    """The user an error was recorded against."""

    @override
    def build_query(self, field_ids: Sequence[ErrorLogID]) -> sa.sql.Select[Any]:
        """Rows written before logs became a user's field carry no user, so they
        resolve to no owner and drop out of the lookup."""
        return sa.select(ErrorLogRow.id, sa.cast(ErrorLogRow.user, GUID(UserID))).where(
            ErrorLogRow.id.in_(field_ids), ErrorLogRow.user.is_not(None)
        )

    @override
    def to_entity_id(self, row: Row[Any]) -> UserID:
        return UserID(row[1])
