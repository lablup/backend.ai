from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "APP_CONFIG_DEFINITION_ENTITY_TYPE",
    "AppConfigDefinitionID",
)


# Raw string mirroring the RBAC-managed EntityType.APP_CONFIG_DEFINITION value.
APP_CONFIG_DEFINITION_ENTITY_TYPE = EntityType("app_config_definition")


class AppConfigDefinitionID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_DEFINITION_ENTITY_TYPE
