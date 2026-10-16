from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeletePartialBulkOpsAction
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.image.updaters import ImageSoftDeleteUpdater


@dataclass(frozen=True)
class PartialBulkDeleteImagesAction(DeletePartialBulkOpsAction[ImageRow, ImageData]):
    """Forget the named images, answering for each one."""

    ids: Sequence[ImageID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_delete_images"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ImageSoftDeleteUpdater]:
        return {image_id: ImageSoftDeleteUpdater(image_id=image_id) for image_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[image_id for image_id in self.ids if image_id in allowed])
