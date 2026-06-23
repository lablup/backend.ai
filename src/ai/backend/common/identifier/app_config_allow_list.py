from typing import NewType
from uuid import UUID

__all__ = ("AppConfigAllowListID",)


AppConfigAllowListID = NewType("AppConfigAllowListID", UUID)
