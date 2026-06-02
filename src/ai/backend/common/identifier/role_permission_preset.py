from typing import NewType
from uuid import UUID

__all__ = ("RolePermissionPresetID",)


RolePermissionPresetID = NewType("RolePermissionPresetID", UUID)
