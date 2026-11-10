from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "AppConfigAllowListEntityType",
    "AppConfigAllowListID",
)


class AppConfigAllowListEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "app_config_allow_list"

    @override
    @classmethod
    def description(cls) -> str:
        return "One app config key a scope type may set, and the rank its fragments merge at."


class AppConfigAllowListID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return AppConfigAllowListEntityType()
