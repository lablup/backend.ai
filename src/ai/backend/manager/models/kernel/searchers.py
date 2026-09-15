"""List-read specs for kernels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class KernelSearcher(Searcher[KernelRow, KernelInfo]):
    """The kernel rows a read returns. Which sessions' kernels these are is the
    operation scope's to say."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelRow)

    @override
    def to_data(self, row: KernelRow) -> KernelInfo:
        return row.to_kernel_info()
