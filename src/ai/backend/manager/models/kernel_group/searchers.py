"""List-read specs for kernel groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.kernel_group.types import KernelGroupData
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.models.kernel_group.searchable_fields import KernelGroupSearchableFields
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class KernelGroupSearcher(Searcher[KernelGroupRow, KernelGroupData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelGroupRow)

    @override
    def to_data(self, row: KernelGroupRow) -> KernelGroupData:
        return KernelGroupSearchableFields.own.to_data(row)
