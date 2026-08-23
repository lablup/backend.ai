"""Id of the login session table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = (
    "LOGIN_SESSION_FIELD_TYPE",
    "LoginSessionID",
)


LOGIN_SESSION_FIELD_TYPE = FieldType("login_session")


class LoginSessionID(FieldIdentifier):
    """A login session's id.

    A session belongs to the user who signed in and is read through them, so the user
    owns the row and the session declares no scope of its own.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return LOGIN_SESSION_FIELD_TYPE
