from typing import NewType
from uuid import UUID

__all__ = ("ErrorLogID",)


ErrorLogID = NewType("ErrorLogID", UUID)
