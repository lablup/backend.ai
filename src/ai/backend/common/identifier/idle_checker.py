from typing import NewType
from uuid import UUID

__all__ = (
    "IdleCheckerBindingID",
    "IdleCheckerID",
)


IdleCheckerID = NewType("IdleCheckerID", UUID)
IdleCheckerBindingID = NewType("IdleCheckerBindingID", UUID)
