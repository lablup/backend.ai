from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.app_config.types import (
    AppConfigAllowListData,
    AppConfigFragmentData,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.specs.purger import EntityBatchPurger, EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class AppConfigAllowListPurger(EntityPurger[AppConfigAllowListRow, AppConfigAllowListData]):
    """Purger for deleting an app config allow-list entry."""

    allow_list_id: AppConfigAllowListID

    @override
    def row_class(self) -> type[AppConfigAllowListRow]:
        return AppConfigAllowListRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return AppConfigAllowListRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.allow_list_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigAllowListRow) -> AppConfigAllowListData:
        return row.to_data()


@dataclass
class AllowListFragmentPurger(EntityBatchPurger[AppConfigFragmentRow, AppConfigFragmentData]):
    """Clears the fragments an allow-list entry leaves behind, each with the RBAC graph
    it left."""

    allow_list_id: AppConfigAllowListID

    @override
    def entity_id(self, row: AppConfigFragmentRow) -> EntityIdentifier:
        return AppConfigFragmentID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AppConfigFragmentRow]]:
        gate = sa.select(AppConfigAllowListRow.config_name, AppConfigAllowListRow.scope_type).where(
            AppConfigAllowListRow.id == self.allow_list_id
        )
        return sa.select(AppConfigFragmentRow).where(
            sa.tuple_(AppConfigFragmentRow.config_name, AppConfigFragmentRow.scope_type).in_(gate)
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigFragmentRow) -> AppConfigFragmentData:
        return row.to_data()
