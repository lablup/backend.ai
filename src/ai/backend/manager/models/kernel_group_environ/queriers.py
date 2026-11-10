from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.kernel_group.types import KernelGroupEnvironData
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkKernelGroupEnvironQuerier(
    BulkFieldQuerier[KernelGroupEnvironRow, KernelGroupEnvironData]
):
    """The environ rows the caller named."""

    @override
    def row_class(self) -> type[KernelGroupEnvironRow]:
        return KernelGroupEnvironRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KernelGroupEnvironRow.id

    @override
    def to_data(self, row: KernelGroupEnvironRow) -> KernelGroupEnvironData:
        return row.to_data()
