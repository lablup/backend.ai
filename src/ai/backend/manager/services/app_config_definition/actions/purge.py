from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_definition import (
    APP_CONFIG_DEFINITION_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.actions.v2.ops.base import PurgeGlobalOpsAction
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.purgers import AppConfigDefinitionPurger
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow


@dataclass
class PurgeAppConfigDefinitionAction(
    PurgeGlobalOpsAction[AppConfigDefinitionRow, AppConfigDefinitionData]
):
    """Unregister a config name."""

    definition_id: AppConfigDefinitionID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_DEFINITION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_app_config_definition"

    @override
    def to_purger(self) -> AppConfigDefinitionPurger:
        return AppConfigDefinitionPurger(definition_id=self.definition_id)
