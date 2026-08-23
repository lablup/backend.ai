"""DataQuerier implementations for the app config definition repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier, DataQuerier


@dataclass
class AppConfigDefinitionQuerier(DataQuerier[AppConfigDefinitionRow, AppConfigDefinitionData]):
    definition_id: AppConfigDefinitionID

    @override
    def row_class(self) -> type[AppConfigDefinitionRow]:
        return AppConfigDefinitionRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return AppConfigDefinitionRow.id

    @override
    def entity_id_value(self) -> AppConfigDefinitionID:
        return self.definition_id

    @override
    def to_data(self, row: AppConfigDefinitionRow) -> AppConfigDefinitionData:
        return row.to_data()


class BulkAppConfigDefinitionQuerier(
    BulkEntityQuerier[AppConfigDefinitionRow, AppConfigDefinitionData]
):
    """The registered config names the caller named."""

    @override
    def row_class(self) -> type[AppConfigDefinitionRow]:
        return AppConfigDefinitionRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return AppConfigDefinitionRow.id

    @override
    def to_data(self, row: AppConfigDefinitionRow) -> AppConfigDefinitionData:
        return row.to_data()
