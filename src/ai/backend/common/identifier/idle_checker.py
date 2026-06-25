from typing import NewType
from uuid import UUID

__all__ = ("IdleCheckerID",)


IdleCheckerID = NewType("IdleCheckerID", UUID)
