from typing import NewType
from uuid import UUID

__all__ = ("StorageNamespaceID",)


StorageNamespaceID = NewType("StorageNamespaceID", UUID)
