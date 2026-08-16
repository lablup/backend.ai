from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.identifier.login_client_type import LoginClientTypeID
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class LoginClientTypePurger(EntityPurger[LoginClientTypeRow, LoginClientTypeData]):
    """Purger for removing a login client type from the catalog."""

    login_client_type_id: LoginClientTypeID

    @override
    def row_class(self) -> type[LoginClientTypeRow]:
        return LoginClientTypeRow

    @override
    def pk_value(self) -> LoginClientTypeID:
        return self.login_client_type_id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.login_client_type_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: LoginClientTypeRow) -> LoginClientTypeData:
        return row.to_dataclass()
