"""Entity type and id of the error logs table."""

from typing import override

from ai.backend.common.data.entity.types import EntityType, FieldIdentifier, FieldType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE

__all__ = (
    "ERROR_LOG_FIELD_TYPE",
    "ErrorLogID",
)


ERROR_LOG_FIELD_TYPE = FieldType("error_log")


class ErrorLogID(FieldIdentifier):
    """A recorded error's id.

    An error is recorded against the user it happened to and is read through them, so
    the user owns the row and the log declares no scope of its own.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ERROR_LOG_FIELD_TYPE

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE
