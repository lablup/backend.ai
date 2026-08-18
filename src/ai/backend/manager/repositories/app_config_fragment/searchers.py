"""Searcher implementations for the app config fragment repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.specs.searcher import Searcher

__all__ = ("RankedAppConfigFragmentSearcher",)


@dataclass
class RankedAppConfigFragmentSearcher(Searcher[AppConfigFragmentRow, AppConfigFragmentData]):
    """Fragments in merge order, which is the ``rank`` of their allow-list entry.

    The fragment row holds no rank of its own, which is what the join is for, on the
    indexed ``(config_name, scope_type)`` FK pair.
    """

    # Not an argument: read in any other order the fragments merge into the wrong config.
    orders: list[QueryOrder] = field(
        default_factory=lambda: [AppConfigAllowListRow.rank.asc()], init=False
    )

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(AppConfigFragmentRow).join(
            AppConfigAllowListRow,
            sa.and_(
                AppConfigAllowListRow.config_name == AppConfigFragmentRow.config_name,
                AppConfigAllowListRow.scope_type == AppConfigFragmentRow.scope_type,
            ),
        )

    @override
    def to_data(self, row: AppConfigFragmentRow) -> AppConfigFragmentData:
        return row.to_data()
