from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class SearchAliasesAction(ImageAction):
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchAliasesActionResult(BaseActionResult):
    data: list[ImageAliasData]
    image_ids: list[ImageID]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
