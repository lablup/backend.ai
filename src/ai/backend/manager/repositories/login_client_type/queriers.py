"""DataQuerier implementations for the login client type repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class LoginClientTypeQuerier(DataQuerier[LoginClientTypeRow, LoginClientTypeData]):
    login_client_type_id: UUID

    @override
    def row_class(self) -> type[LoginClientTypeRow]:
        return LoginClientTypeRow

    @override
    def pk_value(self) -> UUID:
        return self.login_client_type_id

    @override
    def to_data(self, row: LoginClientTypeRow) -> LoginClientTypeData:
        return row.to_dataclass()
