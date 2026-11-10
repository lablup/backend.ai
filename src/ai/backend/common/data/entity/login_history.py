"""Id of the login history table."""

from typing import override

from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)
from ai.backend.common.data.entity.user import UserEntityType

__all__ = (
    "LoginHistoryFieldType",
    "LoginHistoryID",
)


class LoginHistoryFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "login_history"

    @override
    @classmethod
    def description(cls) -> str:
        return "One login attempt recorded for a user."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return UserEntityType


class LoginHistoryID(FieldIdentifier):
    """A login attempt's id.

    An attempt is recorded against the user who made it and is read through them,
    so the user owns the row and the attempt declares no scope of its own.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return LoginHistoryFieldType()
