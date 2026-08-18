"""DataQuerier implementations for app config fragment repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class AppConfigFragmentQuerier(DataQuerier[AppConfigFragmentRow, AppConfigFragmentData]):
    fragment_id: AppConfigFragmentID

    @override
    def row_class(self) -> type[AppConfigFragmentRow]:
        return AppConfigFragmentRow

    @override
    def pk_value(self) -> AppConfigFragmentID:
        return self.fragment_id

    @override
    def to_data(self, row: AppConfigFragmentRow) -> AppConfigFragmentData:
        return row.to_data()
