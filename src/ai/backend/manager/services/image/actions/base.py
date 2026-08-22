from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.image import IMAGE_ENTITY_TYPE, ImageID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class ImageAction(BaseGlobalAction):
    """Base for an operation that names no single image."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return IMAGE_ENTITY_TYPE


@dataclass
class ImageSingleEntityAction(BaseSingleEntityAction):
    """Base for an operation on one image."""

    image_id: ImageID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.image_id
