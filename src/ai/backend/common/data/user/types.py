from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self
from uuid import UUID

from ai.backend.common.types import CIStrEnum


class UserRole(CIStrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


@dataclass(frozen=True)
class UserData:
    user_id: UUID
    is_authorized: bool
    is_admin: bool
    is_superadmin: bool
    role: UserRole
    domain_name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """
        Create UserData from a dictionary.

        Handles conversion of string role to UserRole enum.
        """
        if "role" in data and isinstance(data["role"], str):
            data = {**data, "role": UserRole(data["role"])}
        return cls(**data)
