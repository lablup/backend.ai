"""Searcher implementations for the app config definition repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class AppConfigDefinitionSearcher(Searcher[AppConfigDefinitionRow, AppConfigDefinitionData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(AppConfigDefinitionRow)

    @override
    def to_data(self, row: AppConfigDefinitionRow) -> AppConfigDefinitionData:
        return row.to_data()
