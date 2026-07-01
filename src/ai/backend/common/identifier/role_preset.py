from typing import NewType
from uuid import UUID

__all__ = ("RolePresetID",)


RolePresetID = NewType("RolePresetID", UUID)
