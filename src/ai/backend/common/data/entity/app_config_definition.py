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
        return "An app config key registered for use."


class AppConfigDefinitionID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return AppConfigDefinitionEntityType()
