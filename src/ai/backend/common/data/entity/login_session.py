"""Id of the login session table."""

from typing import override

from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)
from ai.backend.common.data.entity.user import UserEntityType

__all__ = (
    "LoginSessionFieldType",
    "LoginSessionID",
)


class LoginSessionFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "login_session"

    @override
    @classmethod
    def description(cls) -> str:
        return "One live login of a user."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return UserEntityType


class LoginSessionID(FieldIdentifier):
    """A login session's id.

    A session belongs to the user who signed in and is read through them, so the user
    owns the row and the session declares no scope of its own.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return LoginSessionFieldType()
