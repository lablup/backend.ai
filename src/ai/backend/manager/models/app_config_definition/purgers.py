from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class AppConfigDefinitionPurger(EntityPurger[AppConfigDefinitionRow, AppConfigDefinitionData]):
    """Purger for unregistering a config name."""

    definition_id: AppConfigDefinitionID

    @override
    def row_class(self) -> type[AppConfigDefinitionRow]:
        return AppConfigDefinitionRow

    @override
    def pk_value(self) -> AppConfigDefinitionID:
        return self.definition_id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.definition_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AppConfigDefinitionRow) -> AppConfigDefinitionData:
        return row.to_data()
