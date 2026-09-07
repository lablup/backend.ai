from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = (
    "PERMISSION_FIELD_TYPE",
    "PermissionID",
)


PERMISSION_FIELD_TYPE = FieldType("permission")


class PermissionID(FieldIdentifier):
    """The id of one ``permissions`` row — a field row of the role holding it."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return PERMISSION_FIELD_TYPE
