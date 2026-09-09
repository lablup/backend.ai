from typing import NewType, override
from uuid import UUID

from ai.backend.common.data.entity.types import EntityType

__all__ = (
    "AppConfigAllowListEntityType",
    "AppConfigEntityType",
    "AppConfigFragmentEntityType",
    "AppConfigScopeID",
)


class AppConfigAllowListEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "app_config_allow_list"

    @override
    @classmethod
    def description(cls) -> str:
        return "The set of app config keys a scope may set."


class AppConfigFragmentEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "app_config_fragment"

    @override
    @classmethod
    def description(cls) -> str:
        return "One key and value of an app config, set in one scope."


# The merged config a caller reads; the fragments it is merged from are their own type.
class AppConfigEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "app_config"

    @override
    @classmethod
    def description(cls) -> str:
        return "The app config read from a scope, built from its fragments."


# Who an app config fragment belongs to. Polymorphic across scope kinds (domain/user); the
# concrete kind is discriminated by the accompanying ``AppConfigScopeType``, and ``public``
# has no owner at all, so its absence is spelled ``| None`` at each use.
AppConfigScopeID = NewType("AppConfigScopeID", UUID)
