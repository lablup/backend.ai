"""Image search over the scopes images are reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.row import ImageRow

__all__ = ("ScopedSearchImagesAction",)


@dataclass(frozen=True)
class ScopedSearchImagesAction(ScopedSearchOpsAction[ImageRow, ImageData]):
    """Page through the images the named scopes reach, combined with OR.

    Every scope is authorized and every using entity must be readable before the read
    runs, so a caller reaching for one they cannot see is refused rather than served the
    rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ImageEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_images"
