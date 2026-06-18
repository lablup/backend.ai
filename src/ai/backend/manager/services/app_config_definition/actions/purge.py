from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.services.app_config_definition.actions.base import (
    AppConfigDefinitionSingleEntityAction,
    AppConfigDefinitionSingleEntityActionResult,
)


@dataclass
class PurgeAppConfigDefinitionAction(AppConfigDefinitionSingleEntityAction):
    purger: Purger[AppConfigDefinitionRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def target_entity_id(self) -> str:
        return str(self.purger.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG_DEFINITION, str(self.purger.pk_value))


@dataclass
class PurgeAppConfigDefinitionActionResult(AppConfigDefinitionSingleEntityActionResult):
    definition: AppConfigDefinitionData

    @override
    def target_entity_id(self) -> str:
        return str(self.definition.id)
