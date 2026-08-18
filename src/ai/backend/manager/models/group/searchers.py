"""Searcher specs for the groups table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class GroupSearcher(Searcher[GroupRow, GroupData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(GroupRow)

    @override
    def to_data(self, row: GroupRow) -> GroupData:
        return row.to_data()
