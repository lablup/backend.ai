from typing import NewType
from uuid import UUID

__all__ = (
    "SystemSessionEnvironID",
    "SystemSessionEnvironScopeID",
)


SystemSessionEnvironID = NewType("SystemSessionEnvironID", UUID)

# A domain or a project id, discriminated by the accompanying ``SystemSessionEnvironScopeType``;
# ``global`` names none, so its absence is spelled ``| None`` at each use.
SystemSessionEnvironScopeID = NewType("SystemSessionEnvironScopeID", UUID)
