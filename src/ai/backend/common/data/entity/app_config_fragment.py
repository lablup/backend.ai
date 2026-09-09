from typing import override

from ai.backend.common.data.entity.app_config import AppConfigFragmentEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("AppConfigFragmentID",)


class AppConfigFragmentID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return AppConfigFragmentEntityType()
