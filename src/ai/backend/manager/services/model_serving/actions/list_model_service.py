import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import CompactServiceInfo
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceScopeAction,
    ModelServiceScopeActionResult,
)


@dataclass
class ListModelServiceAction(ModelServiceScopeAction):
    session_owener_id: uuid.UUID

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.session_owener_id),)

    name: str | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_model_service"


@dataclass
class ListModelServiceActionResult(ModelServiceScopeActionResult):
    data: list[CompactServiceInfo]
