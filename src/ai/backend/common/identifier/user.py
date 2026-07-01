from typing import NewType
from uuid import UUID

__all__ = ("UserID",)


UserID = NewType("UserID", UUID)
