"""Query specs for the users table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.auth.types import UserData
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.user.row import UserRow


@dataclass
class UserAuthQuerier(DataQuerier[UserRow, UserData]):
    """Reads one user as the authorize flow needs it.

    Its own data type rather than ``UserRow.to_data()``, which drops the password,
    the password's age and the TOTP secret the sign-in checks read.
    """

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
    def to_data(self, row: UserRow) -> UserData:
        return row.to_auth_data()
