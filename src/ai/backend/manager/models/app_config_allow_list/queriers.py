"""DataQuerier implementations for app config allow-list repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier, DataQuerier


@dataclass
class AppConfigAllowListQuerier(DataQuerier[AppConfigAllowListRow, AppConfigAllowListData]):
    allow_list_id: AppConfigAllowListID

    @override
    def row_class(self) -> type[AppConfigAllowListRow]:
        return AppConfigAllowListRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return AppConfigAllowListRow.id

    @override
    def entity_id_value(self) -> AppConfigAllowListID:
        return self.allow_list_id

    @override
    def to_data(self, row: AppConfigAllowListRow) -> AppConfigAllowListData:
        return row.to_data()


class BulkAppConfigAllowListQuerier(
    BulkEntityQuerier[AppConfigAllowListRow, AppConfigAllowListData]
):
    """The allow-list entries the caller named."""

    @override
    def row_class(self) -> type[AppConfigAllowListRow]:
        return AppConfigAllowListRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return AppConfigAllowListRow.id

    @override
    def to_data(self, row: AppConfigAllowListRow) -> AppConfigAllowListData:
        return row.to_data()
