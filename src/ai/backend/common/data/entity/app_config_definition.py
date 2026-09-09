from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "AppConfigDefinitionEntityType",
    "AppConfigDefinitionID",
)


class AppConfigDefinitionEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "app_config_definition"

    @override
    @classmethod
    def description(cls) -> str:
        return "The declaration of an app config key and its value type."


class AppConfigDefinitionID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return AppConfigDefinitionEntityType()
