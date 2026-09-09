from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "AppConfigFragmentEntityType",
    "AppConfigFragmentID",
)


class AppConfigFragmentEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "app_config_fragment"

    @override
    @classmethod
    def description(cls) -> str:
        return "One key and value of an app config, set in one scope."


class AppConfigFragmentID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return AppConfigFragmentEntityType()
