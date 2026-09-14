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
from ai.backend.manager.data.app_config.types import (
    AppConfigAllowListData,
    AppConfigDefinitionData,
    AppConfigFragmentData,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.specs.purger import EntityBatchPurger, EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class AppConfigDefinitionPurger(EntityPurger[AppConfigDefinitionRow, AppConfigDefinitionData]):
    """Purger for unregistering a config name."""

    definition_id: AppConfigDefinitionID

    @override
    def row_class(self) -> type[AppConfigDefinitionRow]:
        return AppConfigDefinitionRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return AppConfigDefinitionRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.definition_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigDefinitionRow) -> AppConfigDefinitionData:
        return row.to_data()


def _config_name_of(definition_id: AppConfigDefinitionID) -> sa.sql.expression.ScalarSelect[str]:
    return (
        sa.select(AppConfigDefinitionRow.config_name)
        .where(AppConfigDefinitionRow.id == definition_id)
        .scalar_subquery()
    )


@dataclass
class DefinitionAllowListPurger(EntityBatchPurger[AppConfigAllowListRow, AppConfigAllowListData]):
    """Clears the allow-list entries a definition leaves behind, each with the RBAC graph
    it left."""

    definition_id: AppConfigDefinitionID

    @override
    def entity_id(self, row: AppConfigAllowListRow) -> EntityIdentifier:
        return AppConfigAllowListID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AppConfigAllowListRow]]:
        return sa.select(AppConfigAllowListRow).where(
            AppConfigAllowListRow.config_name == _config_name_of(self.definition_id)
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigAllowListRow) -> AppConfigAllowListData:
        return row.to_data()


@dataclass
class DefinitionFragmentPurger(EntityBatchPurger[AppConfigFragmentRow, AppConfigFragmentData]):
    """Clears the fragments a definition leaves behind, each with the RBAC graph it left."""

    definition_id: AppConfigDefinitionID

    @override
    def entity_id(self, row: AppConfigFragmentRow) -> EntityIdentifier:
        return AppConfigFragmentID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AppConfigFragmentRow]]:
        return sa.select(AppConfigFragmentRow).where(
            AppConfigFragmentRow.config_name == _config_name_of(self.definition_id)
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigFragmentRow) -> AppConfigFragmentData:
        return row.to_data()
