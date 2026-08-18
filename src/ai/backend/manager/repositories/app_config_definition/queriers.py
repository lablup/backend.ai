"""DataQuerier implementations for the app config definition repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class AppConfigDefinitionQuerier(DataQuerier[AppConfigDefinitionRow, AppConfigDefinitionData]):
    definition_id: AppConfigDefinitionID

    @override
    def row_class(self) -> type[AppConfigDefinitionRow]:
        return AppConfigDefinitionRow

    @override
    def pk_value(self) -> AppConfigDefinitionID:
        return self.definition_id

    @override
    def to_data(self, row: AppConfigDefinitionRow) -> AppConfigDefinitionData:
        return row.to_data()
