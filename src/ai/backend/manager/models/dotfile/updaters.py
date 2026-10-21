from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.dotfile.searchable_fields import DotfileSearchableFields
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater


@dataclass
class DotfileUpdater(DataUpdater[DotfileRow, DotfileData]):
    """Rewrite one dotfile, named by its own id."""

    dotfile_id: DotfileID
    perm: str
    data: str

    @property
    @override
    def row_class(self) -> type[DotfileRow]:
        return DotfileRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return DotfileRow.id

    @override
    def target_id_value(self) -> DotfileID:
        return self.dotfile_id

    @override
    def build_values(self) -> dict[str, Any]:
        return {"perm": self.perm, "data": self.data}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return DotfileSearchableFields.own.to_data(row)


@dataclass
class DotfileDefaultClearUpdater(DataBatchUpdater[DotfileRow, DotfileData]):
    """Clear the default among the user's other dotfiles sharing the named one's path."""

    user_id: UserID
    dotfile_id: DotfileID

    @property
    @override
    def row_class(self) -> type[DotfileRow]:
        return DotfileRow

    @override
    def conditions(self) -> list[QueryCondition]:
        user_id, dotfile_id = self.user_id, self.dotfile_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            target_path = sa.select(DotfileRow.path).where(
                DotfileRow.entity_type == user_id.entity_type(),
                DotfileRow.entity_id == user_id,
                DotfileRow.id == dotfile_id,
            )
            return sa.and_(
                DotfileRow.path == target_path.scalar_subquery(),
                DotfileRow.id != dotfile_id,
                DotfileRow.is_default,
            )

        return [inner]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_default": False}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return DotfileSearchableFields.own.to_data(row)


@dataclass
class DotfileDefaultSetUpdater(DataBatchUpdater[DotfileRow, DotfileData]):
    """Make the named dotfile the default of its path."""

    dotfile_id: DotfileID

    @property
    @override
    def row_class(self) -> type[DotfileRow]:
        return DotfileRow

    @override
    def conditions(self) -> list[QueryCondition]:
        dotfile_id = self.dotfile_id
        return [lambda: DotfileRow.id == dotfile_id]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_default": True}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return DotfileSearchableFields.own.to_data(row)
