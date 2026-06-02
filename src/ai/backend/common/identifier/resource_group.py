import uuid
from typing import NewType

__all__ = (
    "ResourceGroupID",
    "ResourceGroupName",
)


ResourceGroupID = NewType("ResourceGroupID", uuid.UUID)
ResourceGroupName = NewType("ResourceGroupName", str)
