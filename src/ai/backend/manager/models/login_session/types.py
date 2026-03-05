from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ("LoginSecurityPolicy",)


class LoginSecurityPolicy(BaseModel):
    """Login security policy for controlling concurrent session limits.

    Stored as JSONB in the users table via PydanticColumn.
    """

    model_config = ConfigDict(frozen=True)

    max_concurrent_logins: int | None = None
    """Maximum number of concurrent login sessions allowed.

    None means unlimited.
    """
