from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.errors.auth import LoginClientTypeConflict
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class LoginClientTypeCreator(GlobalEntityCreator[LoginClientTypeRow, LoginClientTypeData]):
    """Creator for a login client type — a name in the global login-client catalog."""

    name: str
    description: str | None

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=LoginClientTypeConflict(
                    f"A login client type with name '{self.name}' already exists."
                ),
            ),
        )

    @override
    def build_row(self) -> LoginClientTypeRow:
        return LoginClientTypeRow(
            name=self.name,
            description=self.description,
        )

    @override
    def to_data(self, row: LoginClientTypeRow) -> LoginClientTypeData:
        return row.to_dataclass()
