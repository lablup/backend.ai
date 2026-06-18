from typing import NewType
from uuid import UUID

__all__ = ("AppConfigDefinitionID",)


AppConfigDefinitionID = NewType("AppConfigDefinitionID", UUID)
