from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkKernelQuerier(BulkFieldQuerier[KernelRow, KernelInfo]):
    """The kernels the caller named."""

    @override
    def row_class(self) -> type[KernelRow]:
        return KernelRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KernelRow.id

    @override
    def to_data(self, row: KernelRow) -> KernelInfo:
        return row.to_kernel_info()
