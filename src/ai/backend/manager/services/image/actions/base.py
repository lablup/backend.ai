from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.image import ImageEntityType, ImageID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.models.image.scopes import ImageTarget


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
    """Base for an image read answered within the scopes the caller names.

    An image belongs to the registry it was scanned from, to `public` when that registry
    is registered there, and to the project it was built in. Naming a scope the caller
    holds no permission at refuses the read.
    """

    targets: Sequence[ImageTarget]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ImageEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]


@dataclass
class ImageScopeActionResult(BaseScopeActionResult):
    """A scoped image read names no entity."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
