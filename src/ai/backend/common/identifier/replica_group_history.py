from typing import NewType
from uuid import UUID

__all__ = ("ReplicaGroupHistoryID",)

ReplicaGroupHistoryID = NewType("ReplicaGroupHistoryID", UUID)
