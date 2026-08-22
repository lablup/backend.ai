from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_definition import (
    AppConfigDefinitionID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.purgers import AppConfigDefinitionPurger
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow


@dataclass
class PurgeAppConfigDefinitionAction(
    PurgeEntityOpsAction[AppConfigDefinitionRow, AppConfigDefinitionData]
):
    """Unregister a config name."""

    definition_id: AppConfigDefinitionID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_app_config_definition"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> AppConfigDefinitionPurger:
        return AppConfigDefinitionPurger(definition_id=self.definition_id)
