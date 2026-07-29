from typing import NewType
from uuid import UUID

__all__ = (
    "IdleCheckerAssignmentID",
    "IdleCheckerID",
)


IdleCheckerID = NewType("IdleCheckerID", UUID)
IdleCheckerAssignmentID = NewType("IdleCheckerAssignmentID", UUID)
