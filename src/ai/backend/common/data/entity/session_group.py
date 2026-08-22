from typing import NewType
from uuid import UUID

__all__ = ("SessionGroupID",)


SessionGroupID = NewType("SessionGroupID", UUID)
