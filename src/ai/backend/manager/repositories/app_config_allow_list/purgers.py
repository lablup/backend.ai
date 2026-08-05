from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base.purger import DataPurger
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class AppConfigAllowListPurger(DataPurger[AppConfigAllowListRow, AppConfigAllowListData]):
    """Purger for deleting an app config allow-list entry."""

    allow_list_id: AppConfigAllowListID

    @override
    def row_class(self) -> type[AppConfigAllowListRow]:
        return AppConfigAllowListRow

    @override
    def pk_value(self) -> AppConfigAllowListID:
        return self.allow_list_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigAllowListRow) -> AppConfigAllowListData:
        return row.to_data()
