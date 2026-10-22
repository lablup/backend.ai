from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute, aliased

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
    """Clear the default across the user's dotfiles on the named one's path, the named one
    included. The rows are locked in id order first, so a concurrent switch waits."""

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
            target = aliased(DotfileRow)
            variant = aliased(DotfileRow)
            target_path = sa.select(target.path).where(
                target.entity_type == user_id.entity_type(),
                target.entity_id == user_id,
                target.id == dotfile_id,
            )
            locked = (
                sa.select(variant.id)
                .where(
                    variant.entity_type == user_id.entity_type(),
                    variant.entity_id == user_id,
                    variant.path == target_path.scalar_subquery(),
                )
                .order_by(variant.id)
                .with_for_update()
            )
            return DotfileRow.id.in_(locked)

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
