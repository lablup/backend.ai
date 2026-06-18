from typing import NewType
from uuid import UUID

__all__ = ("AppConfigFragmentID",)


AppConfigFragmentID = NewType("AppConfigFragmentID", UUID)
