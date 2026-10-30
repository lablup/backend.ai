from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.row import ImageRow


@dataclass(frozen=True)
class SearchImagesAction(GlobalSearcherOpsAction[ImageRow, ImageData]):
    """Page through images across every scope, narrowed by the uses the searcher names."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ImageEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_images"
