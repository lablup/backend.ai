"""Internal values the auth service reads off a credential check."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.user import UserID

__all__ = ("UserCredential",)


@dataclass(frozen=True)
class UserCredential:
    """The user whose credential matched, with the password hash stored for them."""

    user_id: UserID
    hashed_password: str
