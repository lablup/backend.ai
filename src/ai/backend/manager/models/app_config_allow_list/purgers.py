from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
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
class AppConfigAllowListsOfDefinitionPurger(
    EntityBatchPurger[AppConfigAllowListRow, AppConfigAllowListData]
):
    """Every allow-list entry under one config name, cleared before the name goes."""

    definition_id: AppConfigDefinitionID

    @override
    def entity_id(self, row: AppConfigAllowListRow) -> EntityIdentifier:
        return AppConfigAllowListID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AppConfigAllowListRow]]:
        config_name = (
            sa.select(AppConfigDefinitionRow.config_name)
            .where(AppConfigDefinitionRow.id == self.definition_id)
            .scalar_subquery()
        )
        return sa.select(AppConfigAllowListRow).where(
            AppConfigAllowListRow.config_name == config_name
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigAllowListRow) -> AppConfigAllowListData:
        return row.to_data()
