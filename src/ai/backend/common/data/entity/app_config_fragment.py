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
        return "One scope's contribution to an app config key, as a JSON document."


class AppConfigFragmentID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return AppConfigFragmentEntityType()
