from collections.abc import Mapping
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.types import ImageID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import (
    ImageStatus,
    ImageWithAgentInstallStatus,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.image.actions.base import ImageScopeAction, ImageScopeActionResult


@dataclass
class GetAllImagesAction(ImageScopeAction):
    """
    Action to retrieve all images, optionally filtered by their status.
    Args:
        status_filter: If provided, only images with a status in this list will be returned.
            If None, images of all statuses will be included.
    """

    status_filter: list[ImageStatus] | None
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
class GetAllImagesActionResult(ImageScopeActionResult):
    data: Mapping[ImageID, ImageWithAgentInstallStatus]
    _scope_type: ScopeType
    _scope_id: str

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id
