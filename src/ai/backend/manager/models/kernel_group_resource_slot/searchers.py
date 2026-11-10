"""List-read specs for kernel group resource slot rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.kernel_group.types import KernelGroupResourceSlotData
from ai.backend.manager.models.kernel_group_resource_slot.row import KernelGroupResourceSlotRow
from ai.backend.manager.models.kernel_group_resource_slot.searchable_fields import (
    KernelGroupResourceSlotSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class KernelGroupResourceSlotSearcher(
    Searcher[KernelGroupResourceSlotRow, KernelGroupResourceSlotData]
):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelGroupResourceSlotRow)

    @override
    def to_data(self, row: KernelGroupResourceSlotRow) -> KernelGroupResourceSlotData:
        return KernelGroupResourceSlotSearchableFields.own.to_data(row)
