from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = (
    "PERMISSION_FIELD_TYPE",
    "PermissionID",
)


PERMISSION_FIELD_TYPE = FieldType("permission")


class PermissionID(FieldIdentifier):
    """One scoped permission's id.

    A field of the role carrying it: a permission row grants nothing on its own, so
    what it belongs to is the role, and what a read of it is answered for is whoever
    holds that role.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return PERMISSION_FIELD_TYPE
