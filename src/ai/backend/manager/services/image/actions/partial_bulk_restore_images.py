from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestorePartialBulkOpsAction
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.image.updaters import ImageRestoreUpdater


@dataclass(frozen=True)
class PartialBulkRestoreImagesAction(RestorePartialBulkOpsAction[ImageRow, ImageData]):
    """Put the named forgotten images back in service, answering for each one."""

    ids: Sequence[ImageID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_restore_images"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ImageRestoreUpdater]:
        return {image_id: ImageRestoreUpdater(image_id=image_id) for image_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[image_id for image_id in self.ids if image_id in allowed])
