from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.image.actions.base import ImageScopeAction, ImageScopeActionResult


@dataclass
class SearchImagesAction(ImageScopeAction):
    querier: BatchQuerier
    user_uuid: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        # Images are scoped to the user
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self.user_uuid

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, self.user_uuid)


@dataclass
class SearchImagesActionResult(ImageScopeActionResult):
    data: list[ImageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    user_uuid: str = ""

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self.user_uuid
