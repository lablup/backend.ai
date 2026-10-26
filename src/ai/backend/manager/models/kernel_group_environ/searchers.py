"""List-read specs for kernel group environ rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.kernel_group.types import KernelGroupEnvironData
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.models.kernel_group_environ.searchable_fields import (
    KernelGroupEnvironSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class KernelGroupEnvironSearcher(Searcher[KernelGroupEnvironRow, KernelGroupEnvironData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelGroupEnvironRow)

    @override
    def to_data(self, row: KernelGroupEnvironRow) -> KernelGroupEnvironData:
        return KernelGroupEnvironSearchableFields.own.to_data(row)
