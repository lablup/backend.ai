"""Searcher implementations for the role preset repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class RolePresetSearcher(Searcher[RolePresetRow, RolePresetData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RolePresetRow)

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()


@dataclass
class RolePermissionPresetSearcher(Searcher[RolePermissionPresetRow, RolePermissionPresetData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RolePermissionPresetRow)

    @override
    def to_data(self, row: RolePermissionPresetRow) -> RolePermissionPresetData:
        return row.to_data()
