from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.base.purger import PurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class AppConfigDefinitionPurgerSpec(PurgerSpec[AppConfigDefinitionRow]):
    """PurgerSpec for deleting an app config definition."""

    definition_id: AppConfigDefinitionID

    @override
    def row_class(self) -> type[AppConfigDefinitionRow]:
        return AppConfigDefinitionRow

    @override
    def pk_value(self) -> AppConfigDefinitionID:
        return self.definition_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
