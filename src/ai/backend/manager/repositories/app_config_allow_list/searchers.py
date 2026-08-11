"""Searcher implementations for app config allow-list repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class AppConfigAllowListSearcher(Searcher[AppConfigAllowListRow, AppConfigAllowListData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(AppConfigAllowListRow)

    @override
    def to_data(self, row: AppConfigAllowListRow) -> AppConfigAllowListData:
        return row.to_data()
