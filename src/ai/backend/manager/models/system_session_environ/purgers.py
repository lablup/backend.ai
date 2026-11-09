"""EntityPurger implementations for the system session environ repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
)

__all__ = ("SystemSessionEnvironPurger",)


@dataclass
class SystemSessionEnvironPurger(EntityPurger[SystemSessionEnvironRow, SystemSessionEnvironData]):
    """Remove one binding, soft-deleted or not, with what it left in the graph."""

    environ_id: SystemSessionEnvironID

    @override
    def row_class(self) -> type[SystemSessionEnvironRow]:
        return SystemSessionEnvironRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return SystemSessionEnvironRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.environ_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: SystemSessionEnvironRow) -> SystemSessionEnvironData:
        return SystemSessionEnvironSearchableFields.own.to_data(row)
