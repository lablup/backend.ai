"""DataUpdater implementations for the login client type repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.login_client_type import LoginClientTypeID
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class LoginClientTypeUpdater(DataUpdater[LoginClientTypeRow, LoginClientTypeData]):
    login_client_type_id: LoginClientTypeID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[LoginClientTypeRow]:
        return LoginClientTypeRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return LoginClientTypeRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.login_client_type_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        return to_update

    @override
    def to_data(self, row: LoginClientTypeRow) -> LoginClientTypeData:
        return row.to_dataclass()
