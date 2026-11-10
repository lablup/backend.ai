from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.queriers import BulkImageQuerier
from ai.backend.manager.models.image.row import ImageRow


@dataclass
class BulkGetImagesAction(PartialBulkGetEntityOpsAction[ImageRow, ImageData]):
    """Read the images the caller named, answering for each id."""

    ids: Sequence[ImageID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_images"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkImageQuerier:
        return BulkImageQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
