"""Searcher specs for the permissions table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class PermissionSearcher(Searcher[PermissionRow, PermissionData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(PermissionRow)

    @override
    def to_data(self, row: PermissionRow) -> PermissionData:
        return row.to_data()
