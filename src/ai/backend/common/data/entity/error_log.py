"""Entity type and id of the error logs table."""

from typing import override

from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)
from ai.backend.common.data.entity.user import UserEntityType

__all__ = (
    "ErrorLogFieldType",
    "ErrorLogID",
)


class ErrorLogFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "error_log"

    @override
    @classmethod
    def description(cls) -> str:
        return "One error recorded for a user."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return UserEntityType


class ErrorLogID(FieldIdentifier):
    """A recorded error's id.

    An error is recorded against the user it happened to and is read through them, so
    the user owns the row and the log declares no scope of its own.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ErrorLogFieldType()
