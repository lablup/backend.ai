from typing import NewType
from uuid import UUID

__all__ = ("SessionID",)


SessionID = NewType("SessionID", UUID)
