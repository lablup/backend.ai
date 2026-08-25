from typing import override

from ai.backend.common.data.entity.app_config import APP_CONFIG_ALLOW_LIST_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("AppConfigAllowListID",)


class AppConfigAllowListID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return APP_CONFIG_ALLOW_LIST_ENTITY_TYPE
