from __future__ import annotations

from dataclasses import dataclass
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
