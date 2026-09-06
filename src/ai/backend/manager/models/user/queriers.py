"""Query specs for the users table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.auth.types import AuthorizingUser
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.user.row import UserRow

__all__ = ("AuthorizingUserQuerier",)


@dataclass
class AuthorizingUserQuerier(DataQuerier[UserRow, AuthorizingUser]):
    """Reads the user an authorize run is for, as that run and its plugins read it."""

    user_id: UserID

    @override
    def row_class(self) -> type[UserRow]:
        return UserRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return UserRow.uuid

    @override
    def entity_id_value(self) -> UserID:
        return self.user_id

    @override
    def to_data(self, row: UserRow) -> AuthorizingUser:
        return AuthorizingUser(
            uuid=row.uuid,
            username=row.username,
            email=row.email,
            status=row.status,
            role=row.role,
            resource_policy=row.resource_policy,
            password_changed_at=row.password_changed_at,
            totp_activated=row.totp_activated,
            totp_key=row.totp_key,
        )
