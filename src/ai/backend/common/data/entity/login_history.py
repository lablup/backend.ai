"""Id of the login history table."""

from typing import override

from ai.backend.common.data.entity.types import EntityType, FieldIdentifier
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE

__all__ = ("LoginHistoryID",)


class LoginHistoryID(FieldIdentifier):
    """A login attempt's id.

    An attempt is recorded against the user who made it and is read through them,
    so the user owns the row and the attempt declares no scope of its own.
    """

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE
