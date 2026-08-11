from typing import NewType
from uuid import UUID

__all__ = (
    "ResourceSlotName",
    "ResourceSlotTypeUUID",
)


ResourceSlotName = NewType("ResourceSlotName", str)
ResourceSlotTypeUUID = NewType("ResourceSlotTypeUUID", UUID)
