from typing import NewType
from uuid import UUID

__all__ = (
    "SystemSessionEnvironID",
    "SystemSessionEnvironScopeID",
)


SystemSessionEnvironID = NewType("SystemSessionEnvironID", UUID)

# The public entity, a domain or a project id, discriminated by the accompanying
# ``SystemSessionEnvironScopeType``.
SystemSessionEnvironScopeID = NewType("SystemSessionEnvironScopeID", UUID)
