from typing import NewType
from uuid import UUID

__all__ = (
    "IdleCheckerAssignmentID",
    "IdleCheckerBindingID",
    "IdleCheckerID",
)


IdleCheckerID = NewType("IdleCheckerID", UUID)
IdleCheckerAssignmentID = NewType("IdleCheckerAssignmentID", UUID)
# Temporary compat alias for the pre-rename DTO package; removed together with it
# in the next stacked PR (service/API layer).
IdleCheckerBindingID = IdleCheckerAssignmentID
