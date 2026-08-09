from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.specs.purger import GlobalEntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class LoginClientTypePurger(GlobalEntityPurger[LoginClientTypeRow, LoginClientTypeData]):
    """Purger for removing a login client type from the catalog."""

    login_client_type_id: UUID

    @override
    def row_class(self) -> type[LoginClientTypeRow]:
        return LoginClientTypeRow

    @override
    def pk_value(self) -> UUID:
        return self.login_client_type_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: LoginClientTypeRow) -> LoginClientTypeData:
        return row.to_dataclass()
