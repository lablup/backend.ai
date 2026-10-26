from __future__ import annotations

from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.kernel_group.types import KernelGroupEnvironData
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier, BulkNestedFieldQuerier


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


class NestedKernelGroupEnvironQuerier(
    BulkNestedFieldQuerier[KernelGroupEnvironRow, KernelGroupEnvironData]
):
    """The environ rows of the kernel groups the caller named, in key order."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelGroupEnvironRow).order_by(KernelGroupEnvironRow.key)

    @override
    def parent_id_column(self) -> InstrumentedAttribute[Any]:
        return KernelGroupEnvironRow.kernel_group_id

    @override
    def to_data(self, row: KernelGroupEnvironRow) -> KernelGroupEnvironData:
        return row.to_data()
