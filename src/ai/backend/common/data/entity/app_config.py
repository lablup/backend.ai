from typing import NewType, override
from uuid import UUID

from ai.backend.common.data.entity.types import EntityType

__all__ = (
    "AppConfigEntityType",
    "AppConfigScopeID",
)


class AppConfigEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "app_config"

    @override
    @classmethod
    def description(cls) -> str:
        return "The value of one app config key, merged from its fragments in every visible scope."


# Who an app config fragment belongs to. Polymorphic across scope kinds (domain/user); the
# concrete kind is discriminated by the accompanying ``AppConfigScopeType``, and ``public``
# has no owner at all, so its absence is spelled ``| None`` at each use.
AppConfigScopeID = NewType("AppConfigScopeID", UUID)
