"""Lookup implementations for the login tables, which are fields of their user."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.login_history import LoginHistoryID
from ai.backend.common.data.entity.login_session import LoginSessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class LoginSessionOwnerLookup(FieldOwnerLookup[LoginSessionID, UserID]):
    """Reads the user each of the login sessions named belongs to."""

    @override
    def build_query(self, field_ids: Sequence[LoginSessionID]) -> sa.sql.Select[Any]:
        return sa.select(LoginSessionRow.id, LoginSessionRow.user_id).where(
            LoginSessionRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> UserID:
        return UserID(value)


class LoginHistoryOwnerLookup(FieldOwnerLookup[LoginHistoryID, UserID]):
    """Reads the user each of the login attempts named was recorded against."""

    @override
    def build_query(self, field_ids: Sequence[LoginHistoryID]) -> sa.sql.Select[Any]:
        return sa.select(LoginHistoryRow.id, LoginHistoryRow.user_id).where(
            LoginHistoryRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> UserID:
        return UserID(value)
