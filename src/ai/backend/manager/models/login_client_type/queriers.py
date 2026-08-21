"""DataQuerier implementations for the login client type repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.login_client_type import LoginClientTypeID
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class LoginClientTypeQuerier(DataQuerier[LoginClientTypeRow, LoginClientTypeData]):
    login_client_type_id: LoginClientTypeID

    @override
    def row_class(self) -> type[LoginClientTypeRow]:
        return LoginClientTypeRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return LoginClientTypeRow.id

    @override
    def entity_id_value(self) -> LoginClientTypeID:
        return self.login_client_type_id

    @override
    def to_data(self, row: LoginClientTypeRow) -> LoginClientTypeData:
        return row.to_dataclass()
