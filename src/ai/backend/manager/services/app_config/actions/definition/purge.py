from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_definition import (
    AppConfigDefinitionID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData


@dataclass(frozen=True)
class PurgeAppConfigDefinitionAction(BaseSingleEntityAction):
    """Unregister a config name. The allow-list entries and fragments the database
    cascades to are cleared in the same transaction, which is why this does not run
    straight against ops."""

    definition_id: AppConfigDefinitionID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.definition_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_app_config_definition"


@dataclass(frozen=True)
class PurgeAppConfigDefinitionActionResult:
    definition_data: AppConfigDefinitionData
