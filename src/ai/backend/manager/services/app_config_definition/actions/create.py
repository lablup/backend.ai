from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.app_config_definition.actions.base import (
    AppConfigDefinitionScopeAction,
    AppConfigDefinitionScopeActionResult,
)


@dataclass
class CreateAppConfigDefinitionAction(AppConfigDefinitionScopeAction):
    creator: Creator[AppConfigDefinitionRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

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
class CreateAppConfigDefinitionActionResult(AppConfigDefinitionScopeActionResult):
    definition: AppConfigDefinitionData

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""
