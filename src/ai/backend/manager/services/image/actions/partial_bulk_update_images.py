from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.image.updaters import ImageUpdater


@dataclass(frozen=True)
class PartialBulkUpdateImagesAction(UpdatePartialBulkOpsAction[ImageRow, ImageData]):
    """Edit the named images' properties, answering for each one."""

    updaters: Sequence[ImageUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_images"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.image_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ImageUpdater]:
        return {updater.image_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.image_id in allowed]
        )
