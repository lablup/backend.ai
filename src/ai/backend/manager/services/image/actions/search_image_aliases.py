from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.image import ImageEntityType, ImageID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.models.image.row import ImageAliasRow
from ai.backend.manager.models.image.scopes import ImageAliasTarget
from ai.backend.manager.models.image.searchers import ImageAliasSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass(frozen=True)
class SearchImageAliasesAction(OperationScopeOpsAction[ImageAliasRow, ImageAliasData]):
    """Page through the aliases one image holds.

    The image is the scope, so ops applies that condition and the caller is answered
    for by their read permission on that image.
    """

    image_id: ImageID
    searcher: ImageAliasSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ImageEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_image_aliases"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.image_id,)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (ImageAliasTarget(image_id=self.image_id),)

    @override
    def to_searcher(self) -> ImageAliasSearcher:
        return self.searcher
