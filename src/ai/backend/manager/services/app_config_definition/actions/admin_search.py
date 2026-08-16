from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_definition import (
    APP_CONFIG_DEFINITION_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.app_config_definition.searchers import (
    AppConfigDefinitionSearcher,
)


@dataclass
class AdminSearchAppConfigDefinitionsAction(
    SearchGlobalOpsAction[AppConfigDefinitionRow, AppConfigDefinitionData]
):
    """Super-admin path: search every registered config definition."""

    searcher: AppConfigDefinitionSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_DEFINITION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_app_config_definitions"

    @override
    def to_searcher(self) -> AppConfigDefinitionSearcher:
        return self.searcher
