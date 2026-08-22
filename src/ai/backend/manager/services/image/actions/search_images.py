from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class SearchImagesAction(ImageAction):
    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_images"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchImagesActionResult:
    data: list[ImageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
