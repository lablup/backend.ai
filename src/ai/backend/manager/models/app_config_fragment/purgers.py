from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.specs.purger import EntityPurger
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
