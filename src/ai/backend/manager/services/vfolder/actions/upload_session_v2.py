import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import (
    EntityType,
    RBACElementType,
    ScopeType,
)
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef


@dataclass
class CreateUploadSessionV2Action(BaseScopeAction):
    """Create an upload session for a vfolder. Policy is resolved internally from user_id."""

    user_id: uuid.UUID
    vfolder_id: uuid.UUID
    path: str
    size: int

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.VFOLDER

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.USER,
            element_id=str(self.user_id),
        )


@dataclass
class CreateUploadSessionV2ActionResult(BaseActionResult):
    token: str
    url: str

    @override
    def entity_id(self) -> str | None:
        return None
