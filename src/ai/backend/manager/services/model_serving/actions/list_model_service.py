import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import CompactServiceInfo
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceScopeAction,
    ModelServiceScopeActionResult,
)


@dataclass
class ListModelServiceAction(ModelServiceScopeAction):
    session_owener_id: uuid.UUID
    name: str | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.session_owener_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, str(self.session_owener_id))


@dataclass
class ListModelServiceActionResult(ModelServiceScopeActionResult):
    data: list[CompactServiceInfo]
    _user_id: uuid.UUID

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self._user_id)
