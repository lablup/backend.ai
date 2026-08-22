from typing import NewType
from uuid import UUID

__all__ = ("VirtualScopeID",)


VirtualScopeID = NewType("VirtualScopeID", UUID)
