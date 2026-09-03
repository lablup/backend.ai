from typing import NewType
from uuid import UUID

__all__ = (
    "FieldPath",
    "PermissionID",
)

# A path into an entity's field catalog: segments of [A-Za-z0-9_]+ joined by ".".
# A path covers its descendants.
FieldPath = NewType("FieldPath", str)

PermissionID = NewType("PermissionID", UUID)
