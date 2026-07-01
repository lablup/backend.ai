"""CreatorSpec implementations for login_client_type repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.errors.auth import LoginClientTypeConflict
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.repositories.base import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class LoginClientTypeCreatorSpec(CreatorSpec[LoginClientTypeRow]):
    """CreatorSpec for login client type creation."""

    name: str
    description: str | None

    @property
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
