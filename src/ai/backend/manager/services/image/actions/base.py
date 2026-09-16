from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.image import ImageEntityType, ImageID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class ImageAction(BaseGlobalAction):
    """Base for an operation that names no single image."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ImageEntityType()


@dataclass
class ImageSingleEntityAction(BaseSingleEntityAction):
    """Base for an operation on one image."""

    image_id: ImageID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.image_id


@dataclass
class ImageScopeAction(BaseScopeAction):
    """Base for an image operation bounded by a scope."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ImageEntityType()


@dataclass
class ImageScopeActionResult(BaseScopeActionResult):
    """A scoped image read names no entity."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
