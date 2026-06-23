from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_definition.actions.base import (
    AppConfigDefinitionScopeAction,
    AppConfigDefinitionScopeActionResult,
)


@dataclass
class ResolveAppConfigDefinitionByConfigNameAction(AppConfigDefinitionScopeAction):
    """Resolve a registered ``config_name`` to its definition (and its id).

    Callers that only hold a ``config_name`` (e.g. the AppConfigFragment scoped search)
    use this to obtain the definition ``id`` the object-level RBAC layer keys on.
    """

    config_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG_DEFINITION, "")


@dataclass
class ResolveAppConfigDefinitionByConfigNameActionResult(AppConfigDefinitionScopeActionResult):
    definition: AppConfigDefinitionData

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""
