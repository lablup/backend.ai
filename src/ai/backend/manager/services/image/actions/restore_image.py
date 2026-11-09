from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.image.updaters import ImageRestoreUpdater


@dataclass(frozen=True)
class RestoreImageByIdAction(RestoreSingleEntityOpsAction[ImageRow, ImageData]):
    """Put one forgotten image back in service."""

    updater: ImageRestoreUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.image_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_image_by_id"

    @override
    def to_updater(self) -> ImageRestoreUpdater:
        return self.updater
