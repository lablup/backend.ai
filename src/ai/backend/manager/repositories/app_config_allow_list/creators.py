"""DataCreator implementations for app config allow-list repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base.creator import DataCreator


@dataclass
class AppConfigAllowListCreator(DataCreator[AppConfigAllowListRow, AppConfigAllowListData]):
    """Creator for an app config allow-list entry.

    ``rank`` is the merge priority every fragment under the entry carries; when not
    given, it falls back to the scope type's default (public=100, domain=200,
    user=300), which orders the scopes so a user's own fragment wins the merge.
    """

    config_name: str
    scope_type: AppConfigScopeType
    rank: int | None = None

    @override
    def build_row(self) -> AppConfigAllowListRow:
        rank = self.rank if self.rank is not None else self.scope_type.default_rank()
        return AppConfigAllowListRow(
            config_name=self.config_name,
            scope_type=self.scope_type,
            rank=rank,
        )

    @override
    def to_data(self, row: AppConfigAllowListRow) -> AppConfigAllowListData:
        return row.to_data()
