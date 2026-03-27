from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class ImageAliasAction(ImageAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.IMAGE_ALIAS
