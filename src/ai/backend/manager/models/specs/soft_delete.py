"""Soft delete and restore updaters shared by every row with ``SoftDeleteMixin``.

``build_values()`` returns a constant, and ``deleted_at`` is the only column written.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, final, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater


@dataclass
class _DeletedAtUpdater[TRow: Base, TData](DataUpdater[TRow, TData], ABC):
    """The row ``target_id`` names in ``target_column`` of ``target_row``, read back
    through ``converter``. ``target_row`` must carry ``SoftDeleteMixin``."""

    target_row: type[TRow]
    target_column: InstrumentedAttribute[Any]
    target_id: EntityIdentifier
    converter: RowDataConverter[TRow, TData]

    @property
    @override
    def row_class(self) -> type[TRow]:
        return self.target_row

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return self.target_column

    @override
    def target_id_value(self) -> EntityIdentifier:
        return self.target_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: TRow) -> TData:
        return self.converter.to_data(row)


@final
@dataclass
class SoftDeleteUpdater[TRow: Base, TData](_DeletedAtUpdater[TRow, TData]):
    """Sets ``deleted_at`` to the current time."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"deleted_at": sa.func.now()}


@final
@dataclass
class RestoreUpdater[TRow: Base, TData](_DeletedAtUpdater[TRow, TData]):
    """Sets ``deleted_at`` back to NULL; the business state stays."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"deleted_at": None}
