"""CreatorSpec implementations for auth (signup) entities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.errors.auth import UserCreationError
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class SignupUserCreatorSpec(CreatorSpec[UserRow]):
    """Inserts a signup user row from the hook-merged column values."""

    user_data: Mapping[str, Any]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=UserCreationError("Failed to create user"),
            ),
        )

    @override
    def build_row(self) -> UserRow:
        return UserRow(**self.user_data)
