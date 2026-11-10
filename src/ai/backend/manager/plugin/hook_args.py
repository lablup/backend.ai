"""The argument each hook event passes to its handlers, one dataclass per event."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID


@dataclass(frozen=True)
class PreSignupHookArgs:
    """``PRE_SIGNUP``"""

    domain_name: DomainName
    email: str
    password: str
    username: str | None
    full_name: str | None
    description: str | None


@dataclass(frozen=True)
class PostSignupHookArgs:
    """``POST_SIGNUP``"""

    email: str
    user_id: UserID
    lang: str


@dataclass(frozen=True)
class VerifyPasswordFormatHookArgs:
    """``VERIFY_PASSWORD_FORMAT``"""

    email: str
    username: str | None
    password: str


@dataclass(frozen=True)
class PostEnqueueSessionHookArgs:
    """``POST_ENQUEUE_SESSION``"""

    session_id: SessionID
