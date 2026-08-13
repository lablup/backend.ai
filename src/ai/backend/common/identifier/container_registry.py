import uuid
from typing import NewType

__all__ = ("ContainerRegistryID",)


ContainerRegistryID = NewType("ContainerRegistryID", uuid.UUID)
