from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_definition import (
    AppConfigDefinitionEntityType,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow


@dataclass(frozen=True)
class AdminSearchAppConfigDefinitionsAction(
    GlobalSearcherOpsAction[AppConfigDefinitionRow, AppConfigDefinitionData]
):
    """Super-admin path: search every registered config definition."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AppConfigDefinitionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_app_config_definitions"
