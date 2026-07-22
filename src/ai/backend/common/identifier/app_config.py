from typing import NewType
from uuid import UUID

__all__ = ("AppConfigScopeIdentifier",)


# Who an app config fragment belongs to. Polymorphic across scope kinds (domain/user); the
# concrete kind is discriminated by the accompanying ``AppConfigScopeType``, and ``public``
# has no owner at all, so its absence is spelled ``| None`` at each use.
AppConfigScopeIdentifier = NewType("AppConfigScopeIdentifier", UUID)
