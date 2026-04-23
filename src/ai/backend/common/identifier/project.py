from typing import NewType
from uuid import UUID

__all__ = ("ProjectID",)


ProjectID = NewType("ProjectID", UUID)
