"""Id of the login history table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("LoginHistoryID",)


LOGIN_HISTORY_FIELD_TYPE = FieldType("login_history")


class LoginHistoryID(FieldIdentifier):
    """A login attempt's id.

    An attempt is recorded against the user who made it and is read through them,
    so the user owns the row and the attempt declares no scope of its own.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return LOGIN_HISTORY_FIELD_TYPE
