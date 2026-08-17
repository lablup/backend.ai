from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_definition import (
    AppConfigDefinitionID,
)
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class AppConfigDefinitionCreator(
    GlobalEntityCreator[AppConfigDefinitionRow, AppConfigDefinitionData]
):
    """Creator for one registered config name."""

    config_name: str

    @override
    def entity_id(self, row: AppConfigDefinitionRow) -> AppConfigDefinitionID:
        return AppConfigDefinitionID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> AppConfigDefinitionRow:
        return AppConfigDefinitionRow(config_name=self.config_name)

    @override
    def to_data(self, row: AppConfigDefinitionRow) -> AppConfigDefinitionData:
        return row.to_data()
