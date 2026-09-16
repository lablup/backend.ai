from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.specs.purger import EntityBatchPurger, EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class AppConfigFragmentPurger(EntityPurger[AppConfigFragmentRow, AppConfigFragmentData]):
    """Purger for one app config fragment."""

    fragment_id: AppConfigFragmentID

    @override
    def row_class(self) -> type[AppConfigFragmentRow]:
        return AppConfigFragmentRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return AppConfigFragmentRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.fragment_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigFragmentRow) -> AppConfigFragmentData:
        return row.to_data()


@dataclass
class AppConfigFragmentsOfDefinitionPurger(
    EntityBatchPurger[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Every fragment written under one config name, cleared before the name goes."""

    definition_id: AppConfigDefinitionID

    @override
    def entity_id(self, row: AppConfigFragmentRow) -> EntityIdentifier:
        return AppConfigFragmentID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AppConfigFragmentRow]]:
        config_name = (
            sa.select(AppConfigDefinitionRow.config_name)
            .where(AppConfigDefinitionRow.id == self.definition_id)
            .scalar_subquery()
        )
        return sa.select(AppConfigFragmentRow).where(
            AppConfigFragmentRow.config_name == config_name
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigFragmentRow) -> AppConfigFragmentData:
        return row.to_data()


@dataclass
class AppConfigFragmentsOfAllowListPurger(
    EntityBatchPurger[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Every fragment one allow-list entry admits, cleared before the entry goes."""

    allow_list_id: AppConfigAllowListID

    @override
    def entity_id(self, row: AppConfigFragmentRow) -> EntityIdentifier:
        return AppConfigFragmentID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AppConfigFragmentRow]]:
        allow_list_key = sa.select(
            AppConfigAllowListRow.config_name, AppConfigAllowListRow.scope_type
        ).where(AppConfigAllowListRow.id == self.allow_list_id)
        return sa.select(AppConfigFragmentRow).where(
            sa.tuple_(AppConfigFragmentRow.config_name, AppConfigFragmentRow.scope_type).in_(
                allow_list_key
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigFragmentRow) -> AppConfigFragmentData:
        return row.to_data()
