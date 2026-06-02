from typing import NewType
from uuid import UUID

__all__ = ("ReplicaID",)

ReplicaID = NewType("ReplicaID", UUID)
