from typing import override

from ai.backend.common.data.entity.app_config import AppConfigAllowListEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("AppConfigAllowListID",)


class AppConfigAllowListID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return AppConfigAllowListEntityType()
