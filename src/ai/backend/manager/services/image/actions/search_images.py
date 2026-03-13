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
    _scope_type: ScopeType
    _scope_id: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id

    @override
    def target_element(self) -> RBACElementRef:
        # Map ScopeType to the corresponding RBACElementType
        scope_element_type_map = {
            ScopeType.USER: RBACElementType.USER,
            ScopeType.PROJECT: RBACElementType.PROJECT,
            ScopeType.DOMAIN: RBACElementType.DOMAIN,
        }
        return RBACElementRef(scope_element_type_map[self._scope_type], self._scope_id)


@dataclass
class SearchImagesActionResult(ImageScopeActionResult):
    data: list[ImageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    _scope_type: ScopeType
    _scope_id: str

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id
