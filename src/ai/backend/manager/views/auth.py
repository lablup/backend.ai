"""Internal values the auth service reads off a credential check."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.user.types import UserStatus

__all__ = ("UserCredential",)


@dataclass(frozen=True)
class UserCredential:
    """The user whose credential matched, with the password hash stored for them."""

    user_id: UserID
    hashed_password: str
    status: UserStatus
    password_changed_at: datetime | None
