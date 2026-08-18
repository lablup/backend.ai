from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_definition import (
    APP_CONFIG_DEFINITION_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.creators import AppConfigDefinitionCreator
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow


@dataclass
class CreateAppConfigDefinitionAction(
    CreateGlobalOpsAction[AppConfigDefinitionRow, AppConfigDefinitionData]
):
    """Register a config name.

    Global-shaped: the definition catalog belongs to no scope. The scope shape it wore
    before always named the global one with an empty id.
    """

    creator: AppConfigDefinitionCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_DEFINITION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_app_config_definition"

    @override
    def to_creator(self) -> AppConfigDefinitionCreator:
        return self.creator
