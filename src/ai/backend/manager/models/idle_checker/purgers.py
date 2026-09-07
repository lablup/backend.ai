from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class IdleCheckerPurger(EntityPurger[IdleCheckerRow, IdleCheckerData]):
    """Purger for removing an idle checker definition from the catalog.

    Purge-shaped: the table carries no lifecycle column, so removing one has always
    been the row leaving the table. Its bindings and session rows follow through
    ``ON DELETE CASCADE``.
    """

    checker_id: IdleCheckerID

    @override
    def entity_id(self) -> IdleCheckerID:
        return self.checker_id

    @override
    def row_class(self) -> type[IdleCheckerRow]:
        return IdleCheckerRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return IdleCheckerRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return row.to_data()
