from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeleteSingleEntityOpsAction
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.image.updaters import ImageSoftDeleteUpdater


@dataclass(frozen=True)
class DeleteImageByIdAction(DeleteSingleEntityOpsAction[ImageRow, ImageData]):
    """Forget one image."""

    updater: ImageSoftDeleteUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.image_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_image_by_id"

    @override
    def to_updater(self) -> ImageSoftDeleteUpdater:
        return self.updater
