"""Image search over the scopes images are reachable from."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.scopes import GlobalImageTarget, ImageTarget
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.image.actions.base import (
    ImageScopeAction,
    ImageScopeActionResult,
)

__all__ = (
    "ScopedSearchImagesAction",
    "ScopedSearchImagesActionResult",
)


@dataclass
class ScopedSearchImagesAction(ImageScopeAction):
    """Page through the images the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest. ``include_global`` names no
    scope and is authorized against none: a registry marked global shows its images to
    everyone.
    """

    targets: Sequence[ImageTarget]
    include_global: bool
    querier: BatchQuerier

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    def operation_scopes(self) -> Sequence[OperationScope]:
        scopes: list[OperationScope] = list(self.targets)
        if self.include_global:
            scopes.append(GlobalImageTarget())
        return scopes

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_images"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ScopedSearchImagesActionResult(ImageScopeActionResult):
    data: list[ImageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
