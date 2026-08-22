from typing import NewType
from uuid import UUID

__all__ = ("ReplicaGroupID",)

ReplicaGroupID = NewType("ReplicaGroupID", UUID)
