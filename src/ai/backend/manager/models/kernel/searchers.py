"""List-read specs for kernels."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.defs import DEFAULT_ROLE
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


@dataclass
class MainKernelSearcher(Searcher[KernelRow, KernelInfo]):
    """The main kernel of ``session_id``."""

    session_id: SessionID = field(kw_only=True)

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelRow).where(
            (KernelRow.session_id == self.session_id) & (KernelRow.cluster_role == DEFAULT_ROLE)
        )

    @override
    def to_data(self, row: KernelRow) -> KernelInfo:
        return row.to_kernel_info()
