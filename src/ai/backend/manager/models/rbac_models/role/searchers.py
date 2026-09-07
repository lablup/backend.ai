"""Searcher implementations for the role repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class RoleSearcher(Searcher[RoleRow, RoleData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RoleRow)

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return row.to_data()
